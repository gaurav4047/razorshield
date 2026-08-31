import uuid
import pytest
from sqlalchemy import select
from app.ai_layer.prompts.batch_pattern_detection import (
    narrate_pattern,
    propose_pattern_candidates,
)
from app.db.models.payment_case import PaymentCase, PaymentMethod
from app.db.session import async_session_factory
from app.domain_logic.pattern_detection import (
    BASELINE_EXCESS_MULTIPLIER,
    MIN_BUCKET_SAMPLE_SIZE,
    detect_systemic_patterns,
)


@pytest.mark.anyio
async def test_3_step_batch_pattern_detection_live():
    batch_uuid = uuid.UUID("c5920dfd-17e4-462b-a915-e183297d84df")

    async with async_session_factory() as db:
        res = await db.execute(
            select(PaymentCase).where(PaymentCase.batch_id == batch_uuid)
        )
        cases = res.scalars().all()

    assert len(cases) == 60

    # Step 1: Gemini candidate proposal
    summary_list = [
        {
            "method": c.method.value,
            "archetype": c.buyer_archetype,
            "classified_root_cause": c.classified_root_cause or c.buyer_archetype,
            "time_ist": c.created_at.strftime("%H:%M:%S"),
            "amount_inr": f"{c.amount_paise / 100:.2f}",
        }
        for c in cases[:20]
    ]
    candidate_output = await propose_pattern_candidates(summary_list)
    assert len(candidate_output.candidate_groupings) >= 2

    # Step 2: Deterministic statistical baseline check
    findings = detect_systemic_patterns(cases, candidate_output.candidate_groupings)
    assert len(findings) >= 1
    npci_finding = findings[0]

    assert npci_finding.bucket_count >= MIN_BUCKET_SAMPLE_SIZE  # 9 >= 5
    assert npci_finding.observed_share >= (npci_finding.expected_share_under_uniform * BASELINE_EXCESS_MULTIPLIER)
    assert npci_finding.total_count == 21
    assert npci_finding.bucket_count == 9

    # Step 3: Gemini narration strictly summarizes verified numbers
    narration_output = await narrate_pattern(npci_finding)
    assert narration_output.narration is not None
    assert len(narration_output.narration) > 15
    assert "9" in narration_output.narration or "42" in narration_output.narration
