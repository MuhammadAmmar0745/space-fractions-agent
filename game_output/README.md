# Space Fractions

A web-based fractions practice game for sixth-grade students, generated from
the project's architecture specification (`Architecture_Documentation.md` and
`Architecture_View.md`).

The player is a starship navigator: each of 10 "transmissions" is a randomly
generated fraction question (addition, subtraction, simplification,
comparison, equivalence) with exact, verified-correct arithmetic. A fresh set
of 10 is generated every time `/questions` is called, so every playthrough is
different. Answering correctly advances the ship along the mission-progress
bar; at the end the player earns a rank based on their score.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in a browser.

## Run with Docker

```bash
docker build -t space-fractions .
docker run -p 5000:5000 space-fractions
```

## Run tests

```bash
pytest
```

## Structure

```
game_output/
├── app.py              # Flask backend: serves the UI, /questions, /play
├── question_generator.py  # Generates 10 fresh randomized fraction questions per call
├── requirements.txt
├── Dockerfile
├── static/
│   ├── index.html
│   ├── css/style.css
│   └── js/game.js        # Screen flow, scoring, question progression
└── tests/
    └── test_game.py       # Question-bank integrity + API tests
```

## Notes

- `/play` optionally logs a game session to PostgreSQL if `DB_HOST` etc. are
  set; if no database is configured it falls back to a placeholder game ID so
  the game still runs with zero setup.
- Questions are generated dynamically by `question_generator.py` using exact
  fraction arithmetic (Python's `fractions.Fraction`), not hardcoded - every
  game gets a different, correctness-verified set of 10 questions.
