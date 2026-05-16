"""Shared validation helpers for multiple-choice question payloads.

Used by Pydantic schemas (e.g. ``QuestionCreate``) so API and CSV import enforce
the same rules. In Python, module and function docstrings are the usual
equivalent of Javadoc — they show up in IDE tooltips and generated docs.
"""

import re
from typing import Dict

VALID_DIFFICULTIES = frozenset({"easy", "medium", "hard"})
CHOICE_KEY_PATTERN = re.compile(r"^[A-Z]$")
MIN_ANSWER_CHOICES = 2
MAX_ANSWER_CHOICES = 8


def normalize_choice_key(key: str) -> str:
    """Return a trimmed, uppercase choice letter (e.g. ``"b"`` → ``"B"``)."""
    return key.strip().upper()


def validate_answer_choices(choices: Dict[str, str]) -> Dict[str, str]:
    """Validate and normalize MCQ options (keys A–Z, 2–8 non-empty choices).

    Raises:
        ValueError: If keys, counts, or choice text are invalid.

    Returns:
        Dict mapping normalized keys to trimmed choice text.
    """
    if not choices:
        raise ValueError("answer_choices must not be empty")
    if len(choices) < MIN_ANSWER_CHOICES:
        raise ValueError(f"answer_choices must have at least {MIN_ANSWER_CHOICES} options")
    if len(choices) > MAX_ANSWER_CHOICES:
        raise ValueError(f"answer_choices must have at most {MAX_ANSWER_CHOICES} options")

    normalized: Dict[str, str] = {}
    for key, text in choices.items():
        choice_key = normalize_choice_key(key)
        if not CHOICE_KEY_PATTERN.match(choice_key):
            raise ValueError(
                f"Invalid choice key '{key}': use single uppercase letters (A, B, C, ...)"
            )
        choice_text = (text or "").strip()
        if not choice_text:
            raise ValueError(f"Choice '{choice_key}' text must not be empty")
        if choice_key in normalized:
            raise ValueError(f"Duplicate choice key '{choice_key}'")
        normalized[choice_key] = choice_text
    return normalized


def validate_correct_answer(correct_answer: str, answer_choices: Dict[str, str]) -> str:
    """Ensure ``correct_answer`` matches a key in normalized ``answer_choices``.

    Returns:
        Uppercase choice key (e.g. ``"B"``).
    """
    normalized = normalize_choice_key(correct_answer)
    if normalized not in answer_choices:
        raise ValueError(
            f"correct_answer '{correct_answer}' must be one of: {', '.join(sorted(answer_choices))}"
        )
    return normalized


def validate_difficulty(difficulty: str) -> str:
    """Normalize and validate difficulty (``easy``, ``medium``, or ``hard``)."""
    normalized = difficulty.strip().lower()
    if normalized not in VALID_DIFFICULTIES:
        allowed = ", ".join(sorted(VALID_DIFFICULTIES))
        raise ValueError(f"difficulty must be one of: {allowed}")
    return normalized
