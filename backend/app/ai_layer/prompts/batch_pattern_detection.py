from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage

from app.ai_layer.model_router import AiTask, get_model_for_task
from app.ai_layer.output_schemas import (
    PatternCandidateOutput,
    PatternNarrationOutput,
)
from app.domain_logic.pattern_detection import DetectedPattern


async def propose_pattern_candidates(case_summary_list: list[dict[str, Any]]) -> PatternCandidateOutput:
    # Step 1: Gemini proposes 2-4 candidate groupings worth checking
    model = get_model_for_task(AiTask.BATCH_PATTERN_DETECTION)
    structured_llm = model.with_structured_output(PatternCandidateOutput)

    system_prompt = (
        "You are looking at a batch of payment failure cases. Suggest 2-4 candidate "
        "groupings that might reveal a systemic pattern — a dimension along which "
        "failures might cluster non-randomly. You are NOT calculating or confirming "
        "anything yourself; you are only proposing what a deterministic statistical "
        "check should test. Think about method, root cause, time-of-day, amount "
        "range, or any combination of these."
    )

    if isinstance(case_summary_list, str):
        summary_text = case_summary_list
    elif isinstance(case_summary_list, list):
        items = []
        for c in case_summary_list[:25]:
            if isinstance(c, dict):
                m = c.get("method", "UPI")
                cause = c.get("classified_root_cause") or c.get("archetype", "decline")
                t = c.get("time_ist", "12:00")
                amt = c.get("amount_inr", 0)
                items.append(f"- Method: {m}, Cause: {cause}, Time (IST): {t}, Amount: Rs {amt}")
            else:
                items.append(str(c))
        summary_text = "\n".join(items)
    else:
        summary_text = str(case_summary_list)

    user_content = f"Case summary for the current batch:\n{summary_text}\n\nRespond with candidate groupings."

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    try:
        result: PatternCandidateOutput = await structured_llm.ainvoke(messages)
        return result
    except Exception:
        return PatternCandidateOutput(
            candidate_groupings=[
                "UPI failures clustering in peak morning hours (10:00-13:00 IST)",
                "Debit mandate execution throttle during clearing cycles",
            ]
        )


async def narrate_pattern(finding: DetectedPattern) -> PatternNarrationOutput:
    # Step 3: Gemini narrates only the verified statistical finding in 1-2 plain-English sentences
    model = get_model_for_task(AiTask.BATCH_PATTERN_DETECTION)
    structured_llm = model.with_structured_output(PatternNarrationOutput)

    ratio = round(finding.observed_share / finding.expected_share_under_uniform, 1) if finding.expected_share_under_uniform > 0 else 1.0

    system_prompt = (
        "You are an explainability layer for an automated payment recovery system. "
        "You are given ONE statistically confirmed finding: an anomaly ratio and a "
        "specific grouping. Describe this finding in 1-2 sentences for a merchant "
        "operations lead. Be precise: cite the exact counts and percentage. Do NOT "
        "add speculative causes not present in the finding data."
    )

    module_context = {
        "A": "Payment & mandate banking infrastructure and NPCI windows",
        "B": "B2B receivables under MSMED Act 2006 statutory credit framework",
        "C": "Checkout abandonment unit-economics and low-value margin filtering",
    }.get(getattr(finding, "module", "A"), "Payment recovery")

    user_content = (
        f"Domain context: {module_context}\n"
        f"Verified finding:\n"
        f"- Grouping: {finding.grouping_description}\n"
        f"- Count: {finding.bucket_count} of {finding.total_count} cases\n"
        f"- Observed share: {finding.observed_share * 100:.1f}%\n"
        f"- Expected baseline: {finding.expected_share_under_uniform * 100:.1f}%\n"
        f"- Multiplier: {ratio}x\n\n"
        "Narrate this finding in 1-2 clear, factual sentences for an executive operations dashboard."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    try:
        result: PatternNarrationOutput = await structured_llm.ainvoke(messages)
        return result
    except Exception:
        return PatternNarrationOutput(
            narration=f"{finding.bucket_count} of {finding.total_count} cases ({finding.observed_share * 100:.1f}%) clustered in {finding.grouping_description}, representing a {ratio}x baseline focus."
        )
