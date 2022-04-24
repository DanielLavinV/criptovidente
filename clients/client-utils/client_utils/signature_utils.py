import hmac
import hashlib


def sign_sha256(secret_key: str, total_params: str) -> str:
    return hmac.new(
        secret_key.encode("utf-8"), total_params.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def sign_sha384(secret_key: str, signature: str) -> str:
    return hmac.new(
        secret_key.encode("utf-8"), signature.encode("utf-8"), hashlib.sha384
    ).hexdigest()
