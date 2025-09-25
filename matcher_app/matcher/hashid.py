"""Генерація стабільних коротких ідентифікаторів."""
from __future__ import annotations

from hashlib import blake2b

CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_BASE = len(CROCKFORD)


def to_crockford(number: int, length: int) -> str:
    """Кодує число у Base32 Crockford фіксованої довжини."""
    if number < 0:
        raise ValueError("number має бути невід'ємним")
    if length <= 0:
        raise ValueError("length має бути додатнім")
    if number == 0:
        digits = [CROCKFORD[0]]
    else:
        digits = []
        while number > 0:
            number, remainder = divmod(number, _BASE)
            digits.append(CROCKFORD[remainder])
    while len(digits) < length:
        digits.append(CROCKFORD[0])
    encoded = "".join(reversed(digits))
    if len(encoded) > length:
        encoded = encoded[-length:]
    return encoded


def hashid(*parts: str, length: int = 12) -> str:
    """Детермінований короткий ідентифікатор на базі BLAKE2b-80."""
    if not parts:
        raise ValueError("Потрібно передати хоча б один елемент")
    length = max(6, min(20, length))
    normalized = "|".join(part.strip().lower() for part in parts)
    digest = blake2b(normalized.encode("utf-8"), digest_size=10).digest()
    number = int.from_bytes(digest, "big")
    return to_crockford(number, length)
