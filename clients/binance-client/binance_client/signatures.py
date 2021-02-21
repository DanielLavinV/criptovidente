import hmac
import hashlib

def sign(secret_key: str, total_params: str) -> str:
    return hmac.new(secret_key.encode('utf-8'), total_params.encode('utf-8'), hashlib.sha256).hexdigest()