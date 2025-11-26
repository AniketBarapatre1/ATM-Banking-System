import hashlib
import os


def hash_pin(pin, salt=None, iterations=600000):
    if salt is None:
        salt = os.urandom(8).hex()
    h = hashlib.pbkdf2_hmac('sha256', pin.encode('utf-8'), bytes.fromhex(salt), iterations).hex()
    return f"{salt}${h}"


def check_pin(pin, stored):
    try:
        salt = stored.rsplit('$', 1)[0]
        return hash_pin(pin, salt) == stored
    except Exception:
            return False


def sanitize_card(raw):
    return ''.join(ch for ch in raw if ch.isdigit())