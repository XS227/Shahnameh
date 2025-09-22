import hashlib
import hmac
import time

def verify_telegram_auth(data: dict, bot_token: str) -> bool:
    received_hash = data.get('hash')
    if not received_hash:
        return False

    auth_data = {k: v for k, v in data.items() if k != 'hash'}
    sorted_data = sorted([f"{k}={v}" for k, v in auth_data.items()])
    data_check_string = '\n'.join(sorted_data)

    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return computed_hash == received_hash
