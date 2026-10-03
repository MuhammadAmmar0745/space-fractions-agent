# Space Fractions — Local Desktop Edition

A native desktop game for practicing fractions, built with Python's
built-in **Tkinter** GUI toolkit.

This version runs entirely on your own computer as a normal desktop
window. There is **no web server, no Flask, and no browser** involved —
you just run one Python file and a game window opens.

## ✨ Features
- Single-instance safeguard: launching the app while a copy is already running shows a message instead of opening a second, overlapping window
- 10 randomized, mathematically-correct fraction questions per playthrough
  (addition, subtraction, simplifying, comparing, and equivalent fractions)
- Instant feedback with a plain-English explanation after every answer
- A final "Mission Report" screen with your score and a rank
- Zero external dependencies to run — just Python's standard library

## 🚀 Quick Start

### Environment Setup
```bash
git clone <your-repo-url>
cd space-fractions-agent/game_output_local
```

Tkinter ships with standard Python on Windows and macOS. On Linux, if the
app fails to start with a Tkinter import error, install it once with:
```bash
sudo apt-get install python3-tk
```

### Run the app
```bash
python space_fractions_app.py
```
A desktop window will open. Click **Start Mission** to begin.

### Run the tests
```bash
pip install -r requirements.txt
pytest
```

### (Optional) Build a real installable .exe
If you want this to run exactly like any other installed application —
double-click an icon, no terminal, no Python command visible — package it
into a standalone executable:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name SpaceFractions space_fractions_app.py
```
This creates `dist/SpaceFractions.exe`. Double-click it to run — no terminal
or Python installation needed on the machine that runs it. Right-click the
`.exe` and choose **Send to > Desktop (create shortcut)** to get a normal
desktop icon, just like any other installed app.

## Project structure
```
game_output_local/
├── space_fractions_app.py   # Tkinter GUI + game flow (start, question, end screens)
├── question_generator.py    # Fraction question generation (shared logic, no GUI code)
├── requirements.txt
├── tests/
│   └── test_game_local.py
└── README.md
```
