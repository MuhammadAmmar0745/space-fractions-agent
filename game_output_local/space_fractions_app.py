"""
space_fractions_app.py
-----------------------
Space Fractions -- LOCAL desktop version.

This is a native desktop application built with Python's built-in Tkinter
GUI toolkit. It runs entirely on your own computer as a normal desktop
window -- there is NO web server, NO Flask, and NO browser involved.

Run it with:
    python space_fractions_app.py
"""

import random
import socket
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox

from question_generator import generate_question_set

# A fixed, unlikely-to-clash local port used purely as a lock: only one
# process on this machine can ever successfully bind to it at a time.
_SINGLE_INSTANCE_PORT = 47921
_lock_socket = None  # kept alive for the whole run; garbage collection would release the lock


def ensure_single_instance():
    """
    Prevent the app from being launched a second time while a copy is
    already running. Without this, each launch opens a brand-new window
    at the same default screen position, so two (or more) copies end up
    stacked exactly on top of each other -- which looks like garbled,
    overlapping text, as if the UI itself were broken.

    This uses a local TCP socket as a cross-platform lock (works the same
    on Windows, macOS, and Linux, with no extra dependencies): the first
    instance binds the port and holds it for as long as it runs; any
    later instance fails to bind, knows another copy is already open,
    tells the user, and exits immediately instead of opening a duplicate
    window.
    """
    global _lock_socket
    _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _lock_socket.bind(("127.0.0.1", _SINGLE_INSTANCE_PORT))
    except OSError:
        # Another instance already holds the lock -- show a message
        # instead of opening a second, overlapping window.
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Space Fractions",
            "Space Fractions is already running.\n\n"
            "Please use the existing window instead of opening a new one.",
        )
        root.destroy()
        sys.exit(0)

BG = "#f3f1fb"
CARD_BG = "#ffffff"
PURPLE = "#6c5ce7"
TEAL = "#17c3a2"
RED = "#e74c3c"
TEXT_DARK = "#2d2a4a"
TEXT_MUTED = "#6b6b80"

TOTAL_QUESTIONS = 10


class SpaceFractionsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Space Fractions - Local Edition")
        self.geometry("700x640")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.title_font = tkfont.Font(family="Segoe UI", size=22, weight="bold")
        self.h2_font = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        self.body_font = tkfont.Font(family="Segoe UI", size=12)
        self.option_font = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        self.small_font = tkfont.Font(family="Segoe UI", size=10)

        self.questions = []
        self.q_index = 0
        self.score = 0
        self.answered = False

        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        self.show_start_screen()

    # ---------- screen helpers ----------
    def _clear(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def _card(self, parent):
        card = tk.Frame(parent, bg=CARD_BG, highlightbackground="#e3e0f5",
                         highlightthickness=1)
        return card

    # ---------- Screen 1: Start ----------
    def show_start_screen(self):
        self._clear()
        wrap = tk.Frame(self.container, bg=BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(wrap, text="🚀", font=("Segoe UI Emoji", 40), bg=BG).pack(pady=(0, 10))
        tk.Label(wrap, text="Space Fractions", font=self.title_font,
                 fg=PURPLE, bg=BG).pack()
        tk.Label(wrap, text="Practice fractions on a mission through space.",
                 font=self.body_font, fg=TEXT_MUTED, bg=BG).pack(pady=(6, 24))

        start_btn = tk.Button(
            wrap, text="Start Mission", font=self.option_font, fg="white",
            bg=PURPLE, activebackground="#5b4bd6", relief="flat",
            padx=30, pady=12, cursor="hand2", command=self.start_game
        )
        start_btn.pack()

    # ---------- Screen 2: Question ----------
    def start_game(self):
        self.questions = generate_question_set(TOTAL_QUESTIONS)
        self.q_index = 0
        self.score = 0
        self.show_question_screen()

    def show_question_screen(self):
        self._clear()
        self.answered = False
        q = self.questions[self.q_index]

        top = tk.Frame(self.container, bg=BG)
        top.pack(fill="x", pady=(0, 14))

        tk.Label(top, text="Sector", font=self.small_font, fg=TEXT_MUTED, bg=BG)\
            .grid(row=0, column=0, sticky="w")
        tk.Label(top, text=f"{self.q_index + 1} / {TOTAL_QUESTIONS}",
                 font=self.small_font, fg=TEXT_DARK, bg=BG)\
            .grid(row=0, column=1, sticky="e")
        top.grid_columnconfigure(1, weight=1)

        progress = tk.Canvas(top, height=8, bg="#e3e0f5", highlightthickness=0)
        progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        top.grid_columnconfigure(0, weight=1)
        self.update_idletasks()
        width = 660
        filled = int(width * (self.q_index / TOTAL_QUESTIONS))
        progress.create_rectangle(0, 0, width, 8, fill="#e3e0f5", width=0)
        progress.create_rectangle(0, 0, filled, 8, fill=TEAL, width=0)

        tk.Label(self.container, text="Score", font=self.small_font,
                 fg=TEXT_MUTED, bg=BG).pack(anchor="w", pady=(10, 0))
        tk.Label(self.container, text=str(self.score), font=self.h2_font,
                 fg=TEXT_DARK, bg=BG).pack(anchor="w")

        card = self._card(self.container)
        card.pack(fill="both", expand=True, pady=(16, 0))
        inner = tk.Frame(card, bg=CARD_BG)
        inner.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(inner, text="INCOMING TRANSMISSION", font=self.small_font,
                 fg="#e08e2f", bg=CARD_BG).pack(anchor="w")
        tk.Label(inner, text=q["prompt"], font=self.h2_font, fg=TEXT_DARK,
                 bg=CARD_BG, wraplength=600, justify="left")\
            .pack(anchor="w", pady=(6, 20))

        self.option_buttons = {}
        grid = tk.Frame(inner, bg=CARD_BG)
        grid.pack(fill="x")
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        options = list(q["options"])
        for i, opt in enumerate(options):
            r, c = divmod(i, 2)
            btn = tk.Button(
                grid, text=opt, font=self.option_font, fg=TEXT_DARK,
                bg="#f6f5fb", activebackground="#e9e6fa", relief="flat",
                padx=10, pady=16, cursor="hand2",
                command=lambda o=opt: self.answer(o)
            )
            btn.grid(row=r, column=c, sticky="nsew", padx=6, pady=6)
            self.option_buttons[opt] = btn

        self.feedback_label = tk.Label(inner, text="", font=self.h2_font,
                                        bg=CARD_BG, wraplength=600, justify="left")
        self.feedback_label.pack(anchor="w", pady=(18, 0))
        self.explanation_label = tk.Label(inner, text="", font=self.body_font,
                                           fg=TEXT_MUTED, bg=CARD_BG,
                                           wraplength=600, justify="left")
        self.explanation_label.pack(anchor="w", pady=(4, 14))

        self.next_btn = tk.Button(
            inner, text="Next Transmission", font=self.option_font, fg=PURPLE,
            bg="#e9e6fa", activebackground="#ddd8f5", relief="flat",
            padx=20, pady=12, cursor="hand2", state="disabled",
            command=self.next_question
        )
        self.next_btn.pack(fill="x")

    def answer(self, chosen):
        if self.answered:
            return
        self.answered = True
        q = self.questions[self.q_index]
        correct = q["answer"]

        for opt, btn in self.option_buttons.items():
            btn.config(state="disabled")
            if opt == correct:
                btn.config(bg=TEAL, fg="white")
            elif opt == chosen:
                btn.config(bg=RED, fg="white")

        if chosen == correct:
            self.score += 1
            self.feedback_label.config(text="Correct! Sector cleared.", fg=TEAL)
        else:
            self.feedback_label.config(text="Not quite.", fg=RED)

        self.explanation_label.config(text=q["explanation"])
        self.next_btn.config(state="normal")

    def next_question(self):
        self.q_index += 1
        if self.q_index >= TOTAL_QUESTIONS:
            self.show_end_screen()
        else:
            self.show_question_screen()

    # ---------- Screen 3: End ----------
    def show_end_screen(self):
        self._clear()
        pct = (self.score / TOTAL_QUESTIONS) * 100
        if pct == 100:
            rank = "Fleet Admiral"
        elif pct >= 75:
            rank = "Commander"
        elif pct >= 50:
            rank = "Pilot"
        elif pct >= 25:
            rank = "Navigator Trainee"
        else:
            rank = "Cadet"

        wrap = tk.Frame(self.container, bg=BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        card = self._card(wrap)
        card.pack(padx=10, pady=10)
        inner = tk.Frame(card, bg=CARD_BG)
        inner.pack(padx=50, pady=40)

        tk.Label(inner, text="Mission Report", font=self.body_font,
                 fg=PURPLE, bg=CARD_BG).pack()
        tk.Label(inner, text=rank, font=self.title_font, fg=TEXT_DARK,
                 bg=CARD_BG).pack(pady=(4, 10))
        tk.Label(inner, text=f"You solved {self.score} of {TOTAL_QUESTIONS} transmissions.",
                 font=self.body_font, fg=TEXT_MUTED, bg=CARD_BG).pack(pady=(0, 20))

        canvas = tk.Canvas(inner, width=160, height=160, bg=CARD_BG, highlightthickness=0)
        canvas.pack()
        canvas.create_oval(10, 10, 150, 150, outline="#e3e0f5", width=12)
        extent = 360 * (self.score / TOTAL_QUESTIONS)
        if extent > 0:
            canvas.create_arc(10, 10, 150, 150, start=90, extent=-extent,
                               outline=TEAL, width=12, style="arc")
        canvas.create_text(80, 80, text=f"{self.score}/{TOTAL_QUESTIONS}",
                            font=self.h2_font, fill=TEXT_DARK)

        tk.Button(inner, text="Fly Again", font=self.option_font, fg="white",
                  bg=PURPLE, activebackground="#5b4bd6", relief="flat",
                  padx=30, pady=12, cursor="hand2",
                  command=self.start_game).pack(pady=(24, 0))


if __name__ == "__main__":
    ensure_single_instance()
    app = SpaceFractionsApp()
    app.mainloop()
