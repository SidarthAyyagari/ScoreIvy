"""Shared validation helpers for multiple-choice question payloads.

Used by Pydantic schemas (e.g. ``QuestionCreate``) so API and CSV import enforce
the same rules. In Python, module and function docstrings are the usual
equivalent of Javadoc — they show up in IDE tooltips and generated docs.
"""

import re
from fractions import Fraction
from typing import Dict, Iterable, List, Optional, Tuple

VALID_DIFFICULTIES = frozenset({"easy", "medium", "hard"})
CHOICE_KEY_PATTERN = re.compile(r"^[A-Z]$")
MIN_ANSWER_CHOICES = 2
MAX_ANSWER_CHOICES = 10

MULTIPLE_CHOICE = "multiple_choice"
NUMERIC_ENTRY = "numeric_entry"
QUESTION_TYPES = frozenset({MULTIPLE_CHOICE, NUMERIC_ENTRY})

NUMERIC_ANSWER_PATTERN = re.compile(r"^-?(\d+(\.\d*)?|\.\d+|\d+/\d+)$")
MAX_NUMERIC_ANSWER_LENGTH = 16


def normalize_numeric_answer(value: str) -> str:
    """Trim a typed numeric answer (``" 3 / 4 "`` → ``"3/4"``) and check its format.

    Accepts integers, decimals (``.75``, ``-2.5``), and fractions (``3/4``).
    """
    normalized = (value or "").replace(" ", "").strip()
    if (
        not normalized
        or len(normalized) > MAX_NUMERIC_ANSWER_LENGTH
        or not NUMERIC_ANSWER_PATTERN.match(normalized)
    ):
        raise ValueError(f"'{value}' is not a valid numeric answer (use e.g. 12, -2.5, .75, or 3/4)")
    if "/" in normalized and int(normalized.split("/")[1]) == 0:
        raise ValueError(f"'{value}' divides by zero")
    return normalized


def numeric_value(value: str) -> Fraction:
    """Exact value of a normalized numeric answer, so ``3/4`` equals ``.75``."""
    return Fraction(value)


def numeric_answer_matches(selected: str, accepted: Iterable[str]) -> bool:
    try:
        selected_value = numeric_value(normalize_numeric_answer(selected))
    except (ValueError, ZeroDivisionError):
        return False
    for answer in accepted:
        try:
            if numeric_value(normalize_numeric_answer(answer)) == selected_value:
                return True
        except (ValueError, ZeroDivisionError):
            continue
    return False


def parse_tag(value: str) -> str:
    """Normalize a ``category:name`` tag string (e.g. ``"System : Renal"`` → ``"system:Renal"``)."""
    category, sep, name = (value or "").partition(":")
    category, name = category.strip().lower(), name.strip()
    if not sep or not category or not name:
        raise ValueError(f"Tag '{value}' must look like category:name (e.g. system:Cardiovascular)")
    return f"{category}:{name}"


def validate_question_type(value: str) -> str:
    normalized = (value or MULTIPLE_CHOICE).strip().lower()
    if normalized not in QUESTION_TYPES:
        raise ValueError(f"question_type must be one of: {', '.join(sorted(QUESTION_TYPES))}")
    return normalized


def validate_question_content(
    question_type: str,
    answer_choices: Optional[Dict[str, str]],
    correct_answer: str,
    accepted_answers: Optional[List[str]],
) -> Tuple[Dict[str, str], str, Optional[List[str]]]:
    """Validate the answer fields for a question's type.

    Returns normalized (answer_choices, correct_answer, accepted_answers).
    """
    if question_type == NUMERIC_ENTRY:
        if answer_choices:
            raise ValueError("numeric_entry questions must not have answer_choices")
        correct = normalize_numeric_answer(correct_answer)
        extras = [normalize_numeric_answer(a) for a in (accepted_answers or []) if (a or "").strip()]
        return {}, correct, extras or None

    if accepted_answers:
        raise ValueError("accepted_answers is only used for numeric_entry questions")
    choices = validate_answer_choices(answer_choices or {})
    return choices, validate_correct_answer(correct_answer, choices), None


def is_answer_correct(
    question_type: str,
    selected: Optional[str],
    correct_answer: str,
    accepted_answers: Optional[List[str]] = None,
) -> bool:
    if not selected:
        return False
    if question_type == NUMERIC_ENTRY:
        return numeric_answer_matches(selected, [correct_answer, *(accepted_answers or [])])
    return selected == correct_answer


def normalize_choice_key(key: str) -> str:
    """Return a trimmed, uppercase choice letter (e.g. ``"b"`` → ``"B"``)."""
    return key.strip().upper()


def validate_answer_choices(choices: Dict[str, str]) -> Dict[str, str]:
    """Validate and normalize MCQ options (keys A–Z, 2–10 non-empty choices).

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
