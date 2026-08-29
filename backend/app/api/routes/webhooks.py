import json
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.webhook_event import RawWebhookEvent
from app.db.session import get_db
from app.razorpay_client.webhook_verify import verify_webhook_signature

router = APIRouter()


@router.post("/razorpay", status_code=status.HTTP_200_OK)
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(None, alias="X-Razorpay-Signature"),
    x_razorpay_event_id: str | None = Header(None, alias="X-Razorpay-Event-Id"),
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.body()
    if not raw_body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty webhook body",
        )

    # 1. Signature Verification: Reject immediately on invalid/missing signature before any json.loads()
    if not x_razorpay_signature or not settings.RAZORPAY_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature or secret configuration",
        )

    if not verify_webhook_signature(
        raw_body=raw_body,
        received_signature=x_razorpay_signature,
        webhook_secret=settings.RAZORPAY_WEBHOOK_SECRET,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # 2. JSON Parsing: Executed strictly after successful signature verification
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {str(exc)}",
        )

    # 3. Event Identification: Use X-Razorpay-Event-Id header (unique per delivery), not underlying entity IDs
    event_id = x_razorpay_event_id or payload.get("event_id") or payload.get("id")
    event_type = payload.get("event", "unknown")

    # 4. Idempotency Check: Return 200 OK without re-inserting if this specific delivery was already processed
    if event_id:
        existing = await db.execute(
            select(RawWebhookEvent).where(RawWebhookEvent.razorpay_event_id == event_id)
        )
        if existing.scalar_one_or_none():
            return {
                "status": "already_received",
                "event_id": event_id,
                "event_type": event_type,
            }

    # 5. Persistence: Record verified event in raw_webhook_events
    webhook_event = RawWebhookEvent(
        razorpay_event_id=event_id,
        event_type=event_type,
        payload=payload,
        signature_verified=True,
        processed=False,
    )
    db.add(webhook_event)
    await db.commit()
    await db.refresh(webhook_event)

    return {
        "status": "ok",
        "event_id": event_id,
        "event_type": event_type,
        "record_id": webhook_event.id,
    }
