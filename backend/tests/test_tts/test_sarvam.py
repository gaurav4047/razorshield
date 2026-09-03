import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from app.config import settings
from app.main import app
from app.db.session import async_session_factory
from app.db.models.batch import Batch
from app.db.models.payment_case import PaymentCase, PaymentCaseStatus, PaymentMethod, PaymentContext
from app.tts.service import generate_hinglish_script, synthesize_hinglish_voice


@pytest.mark.anyio
async def test_hinglish_script_generation():
    # Module A script
    script_a = generate_hinglish_script("A", {
        "method": "UPI",
        "classified_root_cause": "insufficient_balance",
        "amount_paise": 50000,
    })
    assert "UPI" in script_a
    assert "Razorpay" in script_a
    assert "Namaste" in script_a

    # Module B script
    script_b = generate_hinglish_script("B", {
        "buyer_name": "Acme Corp",
        "invoice_number": "INV-999",
        "amount_paise": 15000000,
        "computed_interest_paise": 250000,
        "current_rung": 2,
        "supplier_is_msme": True,
    })
    assert "MSMED Act Section 16" in script_b
    assert "INV-999" in script_b


@pytest.mark.anyio
async def test_sarvam_tts_live_synthesis():
    text = "Namaste, aapka Razorpay payment recovery reminder send kiya gaya hai."
    res = await synthesize_hinglish_voice(text, speaker="priya")
    assert res["status"] == "success"
    assert "audio_base64" in res
    assert len(res["audio_base64"]) > 100
    assert res["mime_type"] == "audio/wav"




@pytest.mark.anyio
async def test_voice_nudge_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with async_session_factory() as db:
            batch = Batch(
                label=f"TTS Test Batch {uuid.uuid4().hex[:6]}",
                description="Testing voice nudge API",
            )
            db.add(batch)
            await db.flush()

            pc = PaymentCase(
                batch_id=batch.id,
                razorpay_payment_id=f"pay_tts_{uuid.uuid4().hex[:8]}",
                method=PaymentMethod.UPI,
                context=PaymentContext.SUBSCRIPTION,
                amount_paise=75000,
                failure_code="U30",
                failure_raw_reason="UPI transaction timed out",
                attempt_number=1,
                retry_count=0,
                status=PaymentCaseStatus.OPEN,
            )
            db.add(pc)
            await db.commit()
            pc_id = pc.id

        # 1. Fetch script preview without synthesis
        resp = await client.get(f"/api/cases/A/{pc_id}/voice-nudge?synthesize=false")
        assert resp.status_code == 200
        data = resp.json()
        assert data["can_generate"] is True
        assert "script_text" in data
        assert "Namaste" in data["script_text"]
        assert data["audio_base64"] is None

        # 2. Fetch with live synthesis
        resp_syn = await client.get(f"/api/cases/A/{pc_id}/voice-nudge?synthesize=true")
        assert resp_syn.status_code == 200
        data_syn = resp_syn.json()
        assert data_syn["can_generate"] is True
        assert data_syn["audio_base64"] is not None
        assert len(data_syn["audio_base64"]) > 100
