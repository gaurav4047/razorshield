import hashlib
import hmac
import json
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from app.config import settings
from app.main import app
from app.razorpay_client.webhook_verify import verify_webhook_signature


def test_verify_webhook_signature_valid():
    secret = "test_webhook_secret_12345"
    payload_bytes = b'{"event":"payment_link.paid","id":"evt_12345"}'
    signature = hmac.new(key=secret.encode(), msg=payload_bytes, digestmod=hashlib.sha256).hexdigest()
    assert verify_webhook_signature(payload_bytes, signature, secret) is True


def test_verify_webhook_signature_invalid():
    secret = "test_webhook_secret_12345"
    payload_bytes = b'{"event":"payment_link.paid","id":"evt_12345"}'
    wrong_signature = "bad_signature_value"
    assert verify_webhook_signature(payload_bytes, wrong_signature, secret) is False


@pytest.mark.anyio
async def test_webhook_endpoint_rejects_missing_signature_with_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        body = b'{"event":"payment.failed","id":"evt_missing_sig"}'
        response = await ac.post("/webhooks/razorpay", content=body)
        assert response.status_code == 401
        assert response.json()["detail"] == "Missing webhook signature or secret configuration"


@pytest.mark.anyio
async def test_webhook_endpoint_rejects_bad_signature_with_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Invalid JSON bytes that would fail json.loads() - proving signature check fails FIRST
        body = b"NOT_EVEN_JSON_CORRUPTED_BYTES"
        headers = {"X-Razorpay-Signature": "invalid_signature"}
        response = await ac.post("/webhooks/razorpay", content=body, headers=headers)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid webhook signature"


@pytest.mark.anyio
async def test_distinct_events_sharing_same_payment_id_are_both_processed():
    # Demonstrates that two distinct lifecycle events sharing the same payment entity ID
    # are both accepted and not deduped against each other because X-Razorpay-Event-Id is unique.
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    shared_payment_id = f"pay_shared_lifecycle_{uuid.uuid4().hex[:8]}"
    evt_auth_id = f"evt_auth_{uuid.uuid4().hex[:12]}"
    evt_cap_id = f"evt_cap_{uuid.uuid4().hex[:12]}"

    # Event 1: payment.authorized
    payload_auth = {
        "event": "payment.authorized",
        "payload": {
            "payment": {
                "entity": {
                    "id": shared_payment_id,
                    "amount": 50000,
                    "status": "authorized",
                }
            }
        },
    }
    raw_auth = json.dumps(payload_auth).encode("utf-8")
    sig_auth = hmac.new(key=secret.encode(), msg=raw_auth, digestmod=hashlib.sha256).hexdigest()

    # Event 2: payment.captured (same underlying payment ID, different event ID)
    payload_cap = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": shared_payment_id,
                    "amount": 50000,
                    "status": "captured",
                }
            }
        },
    }
    raw_cap = json.dumps(payload_cap).encode("utf-8")
    sig_cap = hmac.new(key=secret.encode(), msg=raw_cap, digestmod=hashlib.sha256).hexdigest()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Post first event (authorized)
        resp1 = await ac.post(
            "/webhooks/razorpay",
            content=raw_auth,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": sig_auth,
                "X-Razorpay-Event-Id": evt_auth_id,
            },
        )
        assert resp1.status_code == 200
        assert resp1.json()["status"] == "ok"
        assert resp1.json()["event_id"] == evt_auth_id

        # Post second event (captured) with same underlying payment entity ID
        resp2 = await ac.post(
            "/webhooks/razorpay",
            content=raw_cap,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": sig_cap,
                "X-Razorpay-Event-Id": evt_cap_id,
            },
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "ok"
        assert resp2.json()["event_id"] == evt_cap_id
        # Crucial assertion: record IDs are distinct, neither was discarded as duplicate
        assert resp1.json()["record_id"] != resp2.json()["record_id"]


@pytest.mark.anyio
async def test_webhook_endpoint_idempotency_on_same_event_id():
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    unique_event_id = f"evt_exact_dedup_{uuid.uuid4().hex[:12]}"
    event_payload = {
        "event": "subscription.halted",
        "payload": {
            "subscription": {
                "entity": {
                    "id": "sub_test_halted_555",
                    "status": "halted",
                }
            }
        },
    }
    raw_bytes = json.dumps(event_payload).encode("utf-8")
    valid_sig = hmac.new(key=secret.encode(), msg=raw_bytes, digestmod=hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": valid_sig,
        "X-Razorpay-Event-Id": unique_event_id,
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First delivery
        resp1 = await ac.post("/webhooks/razorpay", content=raw_bytes, headers=headers)
        assert resp1.status_code == 200
        assert resp1.json()["status"] == "ok"

        # Second delivery of identical event ID
        resp2 = await ac.post("/webhooks/razorpay", content=raw_bytes, headers=headers)
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "already_received"
        assert resp2.json()["event_id"] == unique_event_id
