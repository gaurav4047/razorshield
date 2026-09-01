from datetime import datetime
import json
from typing import Any
import uuid
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLogEntry, CaseType
from app.db.session import async_session_factory, get_db

router = APIRouter()


class AuditConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: dict[str, Any]):
        message_str = json.dumps(data, default=str)
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            if dead in self.active_connections:
                self.active_connections.remove(dead)


audit_manager = AuditConnectionManager()


def serialize_audit_entry(entry: AuditLogEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "batch_id": str(entry.batch_id),
        "case_type": entry.case_type.value,
        "case_id": str(entry.case_id),
        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
        "stage": entry.stage.value,
        "rule_suggested_action": entry.rule_suggested_action,
        "ai_reasoning_text": entry.ai_reasoning_text,
        "stopping_rules_checked": entry.stopping_rules_checked or [],
        "final_action": entry.final_action,
        "reason": entry.reason,
        "gross_amount_paise": entry.gross_amount_paise,
        "mdr_paise": entry.mdr_paise,
        "gst_on_mdr_paise": entry.gst_on_mdr_paise,
        "net_amount_paise": entry.net_amount_paise,
        "computed_interest_accrued_paise": entry.computed_interest_accrued_paise,
        "razorpay_reference": entry.razorpay_reference,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


@router.get("", status_code=200)
async def list_audit_logs(
    batch_id: uuid.UUID | None = Query(None),
    case_type: str | None = Query(None),
    case_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLogEntry).order_by(AuditLogEntry.timestamp.desc())

    if batch_id:
        query = query.where(AuditLogEntry.batch_id == batch_id)
    if case_type:
        ct_enum = CaseType(case_type) if case_type in CaseType._value2member_map_ else None
        if ct_enum:
            query = query.where(AuditLogEntry.case_type == ct_enum)
    if case_id:
        query = query.where(AuditLogEntry.case_id == case_id)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    rows = result.scalars().all()

    return {
        "count": len(rows),
        "audit_logs": [serialize_audit_entry(r) for r in rows],
    }


@router.websocket("")
@router.websocket("/ws")
async def audit_websocket_endpoint(websocket: WebSocket, batch_id: str | None = None):
    await audit_manager.connect(websocket)
    try:
        # Keep alive and receive any client ping
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        audit_manager.disconnect(websocket)
    except Exception:
        audit_manager.disconnect(websocket)

