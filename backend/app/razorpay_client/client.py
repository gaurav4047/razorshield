import asyncio
import base64
from typing import Any
import httpx
from app.config import settings

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"


def _get_auth_headers() -> dict[str, str]:
    auth_str = f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    return {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/json",
    }


async def create_payment_link(
    amount_paise: int,
    reference_id: str,
    description: str,
    customer_name: str,
    customer_email: str,
    customer_contact: str,
    accept_partial: bool = False,
    first_min_partial_amount: int | None = None,
    notes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "amount": amount_paise,
        "currency": "INR",
        "reference_id": reference_id,
        "description": description,
        "customer": {
            "name": customer_name,
            "email": customer_email,
            "contact": customer_contact,
        },
        "notify": {"sms": False, "email": False},
        "reminder_enable": False,
        "notes": notes or {},
    }

    if accept_partial:
        payload["accept_partial"] = True
        if first_min_partial_amount:
            payload["first_min_partial_amount"] = first_min_partial_amount

    async with httpx.AsyncClient(timeout=25.0) as client:
        for attempt in range(6):
            resp = await client.post(
                f"{RAZORPAY_API_BASE}/payment_links",
                headers=_get_auth_headers(),
                json=payload,
            )
            if resp.status_code == 429:
                wait_s = 12.0 * (attempt + 1)
                print(f"      [Razorpay Rate Limit] 429 received. Pausing {wait_s:.0f}s for gateway quota refresh (attempt {attempt+1}/6)...", flush=True)
                await asyncio.sleep(wait_s)
                continue
            resp.raise_for_status()
            return resp.json()
        resp.raise_for_status()
        return resp.json()


async def fetch_payment_link(payment_link_id: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{RAZORPAY_API_BASE}/payment_links/{payment_link_id}",
            headers=_get_auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()


async def create_order(
    amount_paise: int,
    receipt: str,
    notes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": receipt,
        "notes": notes or {},
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{RAZORPAY_API_BASE}/orders",
            json=payload,
            headers=_get_auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_order(order_id: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{RAZORPAY_API_BASE}/orders/{order_id}",
            headers=_get_auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()
