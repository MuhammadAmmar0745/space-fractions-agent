"""
Tests for Space Fractions.

Run with:  pytest
"""

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from app import app
from question_generator import generate_question_set


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------- Question generator correctness ----------

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
    """A distractor that equals the correct value (just written differently,
    e.g. an unreduced fraction) would be unfair to mark wrong."""
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
    """Sanity check that questions are actually randomized, not fixed."""
    first = [q["prompt"] for q in generate_question_set(10)]
    second = [q["prompt"] for q in generate_question_set(10)]
    assert first != second


# ---------- Fraction scoring logic (mirrors game.js's handleAnswer) ----------

def check_answer(chosen: str, correct: str) -> bool:
    """Python port of the scoring rule used in static/js/game.js,
    kept here so the core "is this answer correct" logic is unit-testable."""
    return chosen == correct


def test_check_answer_correct_case():
    assert check_answer("3/4", "3/4") is True


def test_check_answer_incorrect_case():
    assert check_answer("2/4", "3/4") is False


# ---------- API endpoints ----------

def test_home_route_serves_index_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Space Fractions" in resp.data


def test_questions_endpoint_returns_ten_questions(client):
    resp = client.get("/questions")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 10


def test_questions_endpoint_returns_fresh_set_each_call(client):
    first = client.get("/questions").get_json()
    second = client.get("/questions").get_json()
    assert [q["prompt"] for q in first] != [q["prompt"] for q in second]


def test_play_endpoint_returns_game_id(client):
    resp = client.get("/play")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "gameId" in data
    assert data["status"] == "started"
