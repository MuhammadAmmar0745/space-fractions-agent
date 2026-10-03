"""
Tests for the LOCAL (Tkinter) version of Space Fractions.

These test the shared question-generation logic (question_generator.py),
which is identical to the one used by the game. No Flask/HTTP involved --
this version has no web server, so there are no API endpoints to test.

Run with:  pytest
"""

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from question_generator import generate_question_set


def _parse(s):
    if "/" not in s:
        return None
    n, d = s.split("/")
    return Fraction(int(n), int(d))


def test_generates_requested_count():
    qs = generate_question_set(10)
    assert len(qs) == 10


def test_every_question_has_required_fields():
    for q in generate_question_set(10):
        assert "id" in q
        assert "prompt" in q
        assert "options" in q
        assert "answer" in q
        assert len(q["options"]) == 4


def test_every_answer_is_one_of_the_options():
    for q in generate_question_set(10):
        assert q["answer"] in q["options"], f"Answer not in options: {q}"


def test_no_duplicate_options_within_a_question():
    for q in generate_question_set(10):
        assert len(q["options"]) == len(set(q["options"])), f"Duplicate options: {q}"


def test_no_wrong_option_is_mathematically_equal_to_the_answer():
    for q in generate_question_set(10):
        correct_val = _parse(q["answer"])
        if correct_val is None:
            continue
        for opt in q["options"]:
            if opt == q["answer"]:
                continue
            opt_val = _parse(opt)
            if opt_val is not None:
                assert opt_val != correct_val, f"Distractor equals correct value: {q}"


def test_consecutive_generations_differ():
    first = [q["prompt"] for q in generate_question_set(10)]
    second = [q["prompt"] for q in generate_question_set(10)]
    assert first != second


def check_answer(chosen: str, correct: str) -> bool:
    """Same scoring rule used inside space_fractions_app.py's answer()."""
    return chosen == correct


def test_check_answer_correct_case():
    assert check_answer("3/4", "3/4") is True


def test_check_answer_incorrect_case():
    assert check_answer("2/4", "3/4") is False


def test_rank_thresholds():
    """Mirrors the rank logic in space_fractions_app.py's show_end_screen()."""
    def rank_for(score, total=10):
        pct = (score / total) * 100
        if pct == 100:
            return "Fleet Admiral"
        elif pct >= 75:
            return "Commander"
        elif pct >= 50:
            return "Pilot"
        elif pct >= 25:
            return "Navigator Trainee"
        return "Cadet"

    assert rank_for(10) == "Fleet Admiral"
    assert rank_for(8) == "Commander"
    assert rank_for(5) == "Pilot"
    assert rank_for(3) == "Navigator Trainee"
    assert rank_for(1) == "Cadet"
