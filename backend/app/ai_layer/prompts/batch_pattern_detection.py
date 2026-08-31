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

    summary_text = "\n".join(
        f"- Method: {c.get('method')}, Cause: {c.get('classified_root_cause') or c.get('archetype')}, "
        f"Time (IST): {c.get('time_ist')}, Amount: Rs {c.get('amount_inr')}"
        for c in case_summary_list[:25]  # representative sample
    )

    user_content = f"Case summary for the current batch:\n{summary_text}\n\nRespond with candidate groupings."

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    result: PatternCandidateOutput = await structured_llm.ainvoke(messages)
    return result


async def narrate_pattern(finding: DetectedPattern) -> PatternNarrationOutput:
    # Step 3: Gemini narrates only the verified statistical finding in 1-2 plain-English sentences
    model = get_model_for_task(AiTask.BATCH_PATTERN_DETECTION)
    structured_llm = model.with_structured_output(PatternNarrationOutput)

    ratio = round(finding.observed_share / finding.expected_share_under_uniform, 1) if finding.expected_share_under_uniform > 0 else 1.0

    system_prompt = (
        "You are given a statistical finding that has already been computed and "
        "verified by deterministic code, including a comparison against what would "
        "be expected by pure chance. Your only job is to phrase it as one or two "
        "clear, plain-English sentences suitable for a prominent dashboard callout. "
        "Do not add any additional claim, number, or pattern beyond what is given to "
        "you — you are a narrator of a verified fact, not an analyst finding new facts."
    )

    user_content = (
        f"Finding: {finding.bucket_count} of {finding.total_count} payment failures "
        f"({finding.observed_share * 100:.1f}%) cluster within {finding.grouping_description}, "
        f"versus an expected {finding.expected_share_under_uniform * 100:.1f}% if failures were "
        f"randomly distributed — roughly {ratio}x the baseline rate."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    result: PatternNarrationOutput = await structured_llm.ainvoke(messages)
    return result
