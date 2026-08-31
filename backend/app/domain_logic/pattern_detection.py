from dataclasses import dataclass
from datetime import timedelta, timezone
from app.db.models.payment_case import PaymentCase, PaymentMethod

MIN_BUCKET_SAMPLE_SIZE = 5
BASELINE_EXCESS_MULTIPLIER = 1.5
IST = timezone(timedelta(hours=5, minutes=30), name="IST")


@dataclass(frozen=True)
class DetectedPattern:
    grouping_description: str
    bucket_count: int
    total_count: int
    observed_share: float
    expected_share_under_uniform: float


def detect_systemic_patterns(
    cases: list[PaymentCase],
    candidate_groupings: list[str] | None = None,
) -> list[DetectedPattern]:
    """
    Step 2: Deterministic statistical baseline evaluation against uniform distribution.
    Computes real observed share vs expected share under uniform distribution.
    Flags only if bucket_count >= 5 AND observed_share >= 1.5x expected baseline.
    """
    findings: list[DetectedPattern] = []
    if not cases:
        return findings

    upi_cases = [c for c in cases if c.method == PaymentMethod.UPI]
    total_upi = len(upi_cases)

    # 1. NPCI Execution Window Check (10:00-13:00 IST = 3h / 24h = 12.5% expected baseline)
    expected_npci_share = 3.0 / 24.0  # 0.125 (12.5%)

    if total_upi > 0:
        npci_window_cases = []
        for c in upi_cases:
            ist_dt = c.created_at.astimezone(IST)
            if 10 <= ist_dt.hour < 13:
                npci_window_cases.append(c)

        bucket_count = len(npci_window_cases)
        observed_share = bucket_count / float(total_upi)

        # Flag only if bucket_count >= 5 AND observed_share >= 1.5x expected baseline (18.75%)
        if (
            bucket_count >= MIN_BUCKET_SAMPLE_SIZE
            and observed_share >= (expected_npci_share * BASELINE_EXCESS_MULTIPLIER)
        ):
            findings.append(
                DetectedPattern(
                    grouping_description="UPI failures clustering inside 10:00-13:00 IST NPCI peak window",
                    bucket_count=bucket_count,
                    total_count=total_upi,
                    observed_share=round(observed_share, 4),
                    expected_share_under_uniform=round(expected_npci_share, 4),
                )
            )

    return findings
