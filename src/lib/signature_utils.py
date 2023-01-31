from nacl.signing import SigningKey, VerifyKey

import json


def generate():
    skey = SigningKey.generate()
    vkey = skey.verify_key

    skey_hex, vkey_hex = skey.encode().hex(), vkey.encode().hex()

    return skey_hex, vkey_hex


def sign(skey_hex: str, message_hex: str):
    skey = SigningKey(bytes.fromhex(skey_hex))

    signed = skey.sign(bytes.fromhex(message_hex))

    return signed


def verify(vkey_hex: str, message_hex: str, signature_hex: str):
    vkey = VerifyKey(bytes.fromhex(vkey_hex))

    return vkey.verify(
        bytes.fromhex(message_hex),
        bytes.fromhex(signature_hex),
    )