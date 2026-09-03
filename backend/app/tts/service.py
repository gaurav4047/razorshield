from typing import Any
import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from app.ai_layer.model_router import AiTask, get_model_for_task
from app.config import settings

SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"


async def draft_dynamic_hinglish_voice_script(module: str, case_data: dict[str, Any]) -> str:
    # Use AI (Gemini / Groq) to dynamically craft natural Hinglish copy
    try:
        model = get_model_for_task(AiTask.MESSAGE_DRAFTING)
        system_prompt = (
            "You are an expert conversational financial recovery agent in India. "
            "Draft a 2-sentence polite, concise Hinglish voice script (in Roman/Latin script, e.g. 'Namaste Sarthak ji...') "
            "for an automated phone audio note.\n"
            "Requirements:\n"
            "- Mention the person or business name, the exact amount, and the recovery context.\n"
            "- State that a secure Razorpay link has been shared to complete the payment.\n"
            "- Keep the length between 25 and 35 words so audio synthesis is under 15 seconds.\n"
            "- Output ONLY the spoken text, no quotes, no extra formatting."
        )

        amount_inr = f"{float(case_data.get('amount_paise', 0)) / 100:,.2f}"

        if module == "A":
            method = str(case_data.get("method", "card")).upper()
            root_cause = str(case_data.get("classified_root_cause") or case_data.get("failure_raw_reason") or "network issue").replace("_", " ")
            user_content = f"Customer Name: {case_data.get('customer_name', 'Customer')}, Payment Method: {method}, Amount: Rs {amount_inr}, Root Cause: {root_cause}"
        elif module == "B":
            interest_paise = case_data.get("computed_interest_paise") or 0
            interest_inr = f"{float(interest_paise) / 100:,.2f}"
            user_content = (
                f"Buyer Company: {case_data.get('buyer_name', 'Valued Partner')}, Invoice Number: {case_data.get('invoice_number', 'INV-101')}, "
                f"Principal Amount: Rs {amount_inr}, Statutory MSMED Section 16 Interest: Rs {interest_inr}, Escalation Rung: {case_data.get('current_rung', 1)}"
            )
        else:
            user_content = f"Customer Name: {case_data.get('customer_name', 'Shopper')}, Abandoned Cart Amount: Rs {amount_inr}"

        res = await model.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ])
        content = res.content if hasattr(res, "content") else str(res)
        cleaned = str(content).strip().strip('"')
        if len(cleaned) > 20:
            return cleaned
    except Exception:
        pass

    # Deterministic fallback if AI API is unreachable
    return generate_hinglish_script(module, case_data)


def generate_hinglish_script(module: str, case_data: dict[str, Any]) -> str:

    module = module.upper()

    if module == "A":
        method = str(case_data.get("method", "card")).upper()
        root_cause = str(case_data.get("classified_root_cause") or case_data.get("failure_raw_reason") or "network issue")
        root_cause_clean = root_cause.replace("_", " ")
        amount_inr = f"{float(case_data.get('amount_paise', 0)) / 100:,.2f}"

        return (
            f"Namaste, aapka {amount_inr} rupees ka {method} subscription payment decline ho gaya hai "
            f"due to {root_cause_clean}. Humne aapke registered mobile par ek alternate Razorpay payment link send kiya hai. "
            f"Kripya link open karke payment complete karein. Dhanyawaad."
        )

    elif module == "B":
        buyer_name = case_data.get("buyer_name", "Valued Partner")
        invoice_num = case_data.get("invoice_number", "INV-101")
        amount_inr = f"{float(case_data.get('amount_paise', 0)) / 100:,.2f}"
        interest_paise = case_data.get("computed_interest_paise") or 0
        interest_inr = f"{float(interest_paise) / 100:,.2f}"
        current_rung = case_data.get("current_rung", 1)
        supplier_is_msme = bool(case_data.get("supplier_is_msme", True))

        if current_rung >= 2 and supplier_is_msme and interest_paise > 0:
            total_inr = f"{(float(case_data.get('amount_paise', 0)) + float(interest_paise)) / 100:,.2f}"
            return (
                f"Namaste, {buyer_name} accounts department ke liye urgent call hai regarding invoice {invoice_num}. "
                f"Principal amount {amount_inr} rupees par MSMED Act Section 16 ke tahet {interest_inr} rupees statutory compound interest "
                f"accrue ho chuka hai. Total payable amount {total_inr} rupees hai. Kripya attached payment link se aaj hi clear karein."
            )
        elif current_rung == 4:
            return (
                f"Namaste, {buyer_name} ke liye final demand notice hai regarding invoice {invoice_num} for {amount_inr} rupees. "
                f"MSME Samadhaan portal par statutory filing prepare ho rahi hai. Kripya legal escalation se pehle payment complete karein."
            )
        else:
            return (
                f"Namaste, {buyer_name} accounts team ke liye reminder hai regarding invoice {invoice_num} of {amount_inr} rupees. "
                f"Invoice ki statutory due date nikal chuki hai. Kripya attached Razorpay link se payment settle karein. Dhanyawaad."
            )

    elif module == "C":
        customer_name = case_data.get("customer_name", "Customer")
        amount_inr = f"{float(case_data.get('amount_paise', 0)) / 100:,.2f}"
        return (
            f"Namaste {customer_name} ji, aapka {amount_inr} rupees ka cart checkout incomplete reh gaya tha. "
            f"Humne aapka order reserve rakha hai. Aap is link par click karke 1-click me payment complete kar sakte hain. Dhanyawaad."
        )

    return "Namaste, aapka payment recovery notice send kiya gaya hai. Kripya attached Razorpay link se complete karein."


import base64
import os

AUDIO_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "audio")
os.makedirs(AUDIO_STORAGE_DIR, exist_ok=True)


def get_stored_audio_info(module: str, case_id: str, speaker: str) -> dict[str, str] | None:
    filename = f"{module.lower()}_{str(case_id)}_{speaker}.wav"
    file_path = os.path.join(AUDIO_STORAGE_DIR, filename)
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return {
            "filename": filename,
            "audio_url": f"/audio/{filename}",
            "file_path": file_path,
        }
    return None


def save_audio_to_storage(module: str, case_id: str, speaker: str, base64_data: str) -> str:
    filename = f"{module.lower()}_{str(case_id)}_{speaker}.wav"
    file_path = os.path.join(AUDIO_STORAGE_DIR, filename)
    audio_bytes = base64.b64decode(base64_data)
    with open(file_path, "wb") as f:
        f.write(audio_bytes)
    return f"/audio/{filename}"


async def synthesize_hinglish_voice(
    text: str,
    speaker: str = "priya",
    pace: float = 1.0,
    module: str | None = None,
    case_id: str | None = None,
) -> dict[str, Any]:
    if not settings.SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY is not configured in environment settings")

    headers = {
        "api-subscription-key": settings.SARVAM_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model": "bulbul:v3",
        "language_code": "hi-IN",
        "speaker": speaker,
        "pace": pace,
        "speech_sample_rate": 24000,
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(SARVAM_TTS_URL, headers=headers, json=payload)
        if resp.status_code != 200:
            raise ValueError(f"Sarvam API {resp.status_code}: {resp.text}")
        data = resp.json()
        audios = data.get("audios", [])

        if not audios:
            raise ValueError("No audio returned from Sarvam TTS API")

        base64_audio = audios[0]
        audio_url = None
        if module and case_id:
            audio_url = save_audio_to_storage(module, str(case_id), speaker, base64_audio)

        return {
            "status": "success",
            "audio_base64": base64_audio,
            "audio_url": audio_url,
            "text": text,
            "speaker": speaker,
            "mime_type": "audio/wav",
        }

