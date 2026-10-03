"""
question_generator.py
----------------------
Generates fresh, randomized, mathematically-correct fraction questions
every time it's called - so every playthrough gets a different set of
10 questions, in a different order.

Uses Python's `fractions.Fraction` for exact arithmetic, so results are
always correctly reduced (no rounding bugs).
"""

import random
from fractions import Fraction

SPACE_CONTEXTS = [
    "Commander! An asteroid approaches. Solve:",
    "Shield power recalculation needed:",
    "The alien decoder needs this simplified:",
    "Fuel gauge check:",
    "Captain's log entry:",
    "Star chart correction:",
    "Cargo bay ratio:",
    "Life support recalibration:",
    "Navigation beacon signal:",
    "Mission control transmission:",
]


def _f(fr: Fraction) -> str:
    return f"{fr.numerator}/{fr.denominator}"


def _random_fraction(max_den=12):
    d = random.randint(2, max_den)
    n = random.randint(1, d - 1)
    return Fraction(n, d)


def _distractors(correct: Fraction, count=3):
    """Generates plausible-but-wrong fraction strings near the correct answer.

    Deliberately avoids any distractor that is mathematically EQUAL to the
    correct answer (just written differently, e.g. an unreduced form) -
    marking that wrong would be unfair to a student who reasoned correctly.
    """
    seen = {_f(correct)}
    out = []
    attempts = 0
    while len(out) < count and attempts < 60:
        attempts += 1
        strategy = random.choice(["shift_num", "shift_den", "swap"])
        n, d = correct.numerator, correct.denominator
        if strategy == "shift_num":
            n2 = max(1, n + random.choice([-2, -1, 1, 2]))
            cand_val = Fraction(n2, d)
            cand = f"{n2}/{d}"
        elif strategy == "shift_den":
            d2 = max(2, d + random.choice([-2, -1, 1, 2]))
            cand_val = Fraction(n, d2)
            cand = f"{n}/{d2}"
        else:  # swap numerator/denominator-ish mistake
            n3, d3 = (d, n) if n != d else (n + 1, d)
            cand_val = Fraction(n3, d3)
            cand = f"{n3}/{d3}"
        if cand not in seen and cand_val != correct:
            seen.add(cand)
            out.append(cand)
    # top up with plain random fractions if still short
    while len(out) < count:
        f = _random_fraction()
        s = _f(f)
        if s not in seen and f != correct:
            seen.add(s)
            out.append(s)
    return out


def _make_options(correct: Fraction):
    opts = [_f(correct)] + _distractors(correct, 3)
    random.shuffle(opts)
    return opts


def gen_addition_same_denominator():
    d = random.choice([4, 5, 6, 8, 10])
    n1 = random.randint(1, d - 2)
    n2 = random.randint(1, d - n1 - 1)
    a, b = Fraction(n1, d), Fraction(n2, d)
    result = a + b
    prompt = f"{random.choice(SPACE_CONTEXTS)} {_f(a)} + {_f(b)} ="
    explanation = f"Same denominator - just add the numerators: {_f(a)} + {_f(b)} = {n1+n2}/{d}" + (
        f", which simplifies to {_f(result)}." if Fraction(n1 + n2, d) != result else "."
    )
    return prompt, _make_options(result), _f(result), explanation


def gen_addition_diff_denominator():
    d1, d2 = random.sample([2, 3, 4, 5, 6], 2)
    n1 = random.randint(1, d1 - 1)
    n2 = random.randint(1, d2 - 1)
    a, b = Fraction(n1, d1), Fraction(n2, d2)
    result = a + b
    if result >= 1:  # keep it approachable for 6th grade
        return gen_addition_same_denominator()
    prompt = f"{random.choice(SPACE_CONTEXTS)} {_f(a)} + {_f(b)} ="
    explanation = f"Find a common denominator first, then add: {_f(a)} + {_f(b)} = {_f(result)}."
    return prompt, _make_options(result), _f(result), explanation


def gen_subtraction_same_denominator():
    d = random.choice([4, 5, 6, 8, 10])
    n1 = random.randint(2, d - 1)
    n2 = random.randint(1, n1 - 1)
    a, b = Fraction(n1, d), Fraction(n2, d)
    result = a - b
    prompt = f"{random.choice(SPACE_CONTEXTS)} {_f(a)} - {_f(b)} ="
    explanation = f"Same denominator - subtract the numerators: {_f(a)} - {_f(b)} = {n1-n2}/{d}" + (
        f", which simplifies to {_f(result)}." if Fraction(n1 - n2, d) != result else "."
    )
    return prompt, _make_options(result), _f(result), explanation


def gen_simplify():
    g = random.randint(2, 4)
    reduced_n = random.randint(1, 5)
    reduced_d = reduced_n + random.randint(1, 5)
    n2, d2 = reduced_n * g, reduced_d * g
    result = Fraction(reduced_n, reduced_d)
    prompt = f"{random.choice(SPACE_CONTEXTS)} Simplify {n2}/{d2} ="
    explanation = f"Divide top and bottom by {g}: {n2}/{d2} = {_f(result)}."
    return prompt, _make_options(result), _f(result), explanation


def gen_compare():
    a = _random_fraction(8)
    b = _random_fraction(8)
    tries = 0
    while a == b and tries < 10:
        b = _random_fraction(8)
        tries += 1
    bigger = a if a > b else b
    prompt = f"{random.choice(SPACE_CONTEXTS)} Which fraction is bigger, {_f(a)} or {_f(b)}?"
    options = [_f(a), _f(b), "They are equal", "Cannot tell"]
    random.shuffle(options)
    explanation = f"Convert to a common denominator to compare: {_f(bigger)} is the larger fraction."
    return prompt, options, _f(bigger), explanation


def gen_equivalent():
    n, d = random.randint(1, 4), random.randint(2, 6)
    while n >= d:
        n, d = random.randint(1, 4), random.randint(2, 6)
    base = Fraction(n, d)
    k = random.choice([2, 3, 4])
    correct = f"{n*k}/{d*k}"
    prompt = f"{random.choice(SPACE_CONTEXTS)} Which fraction is equivalent to {_f(base)}?"
    wrong = [f"{n*k+1}/{d*k}", f"{n*k}/{d*k+1}", f"{n+k}/{d+k}"]
    options = [correct] + wrong[:3]
    random.shuffle(options)
    explanation = f"Multiply top and bottom by {k}: {_f(base)} = {correct}."
    return prompt, options, correct, explanation


GENERATORS = [
    gen_addition_same_denominator,
    gen_addition_diff_denominator,
    gen_subtraction_same_denominator,
    gen_simplify,
    gen_compare,
    gen_equivalent,
]


def generate_question_set(count: int = 10) -> list[dict]:
    """Generates `count` fresh, randomized questions with unique prompts."""
    questions = []
    seen_prompts = set()
    attempts = 0
    while len(questions) < count and attempts < count * 8:
        attempts += 1
        gen_fn = random.choice(GENERATORS)
        prompt, options, answer, explanation = gen_fn()
        if prompt in seen_prompts:
            continue
        if answer not in options:  # safety net - should never happen, but never ship a broken question
            continue
        if len(set(options)) != len(options):
            continue
        seen_prompts.add(prompt)
        questions.append({
            "id": len(questions) + 1,
            "prompt": prompt,
            "options": options,
            "answer": answer,
            "explanation": explanation,
        })
    return questions
