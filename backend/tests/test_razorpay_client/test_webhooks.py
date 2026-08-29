import hashlib
import hmac
import json
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
async def test_webhook_endpoint_idempotency():
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    event_payload = {
        "id": "evt_idempotency_test_999",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_idempotency_999",
                    "amount": 10000,
                    "status": "failed",
                }
            }
        },
    }
    raw_bytes = json.dumps(event_payload).encode("utf-8")
    valid_sig = hmac.new(key=secret.encode(), msg=raw_bytes, digestmod=hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": valid_sig,
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First delivery
        resp1 = await ac.post("/webhooks/razorpay", content=raw_bytes, headers=headers)
        assert resp1.status_code == 200
        assert resp1.json()["status"] in ("ok", "already_received")

        # Second delivery with identical event ID (Idempotency test)
        resp2 = await ac.post("/webhooks/razorpay", content=raw_bytes, headers=headers)
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "already_received"
        assert resp2.json()["event_id"] == "evt_idempotency_test_999"
