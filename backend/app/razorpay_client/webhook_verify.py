import hashlib
import hmac


def verify_webhook_signature(raw_body: bytes, received_signature: str, webhook_secret: str) -> bool:
    expected_signature = hmac.new(
        key=webhook_secret.encode(),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_signature, received_signature)
