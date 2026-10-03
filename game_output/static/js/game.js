/* ==========================================================
   Space Fractions - game.js
   Fetches questions from the backend, drives screen transitions,
   scores answers, and advances through the full question set.

   This fixes the earlier bug where only the first question showed:
   the game now tracks a currentIndex and explicitly re-renders the
   next question instead of stopping after question 1.
   ========================================================== */

(function () {
  "use strict";

  let questions = [];
  let currentIndex = 0;
  let score = 0;

  const screens = {
    menu: document.getElementById("screen-menu"),
    question: document.getElementById("screen-question"),
    end: document.getElementById("screen-end"),
  };

  const el = {
    hudSector: document.getElementById("hud-sector"),
    hudScore: document.getElementById("hud-score"),
    progressFill: document.getElementById("progress-fill"),
    progressShip: document.getElementById("progress-ship"),
    prompt: document.getElementById("question-prompt"),
    options: document.getElementById("options-container"),
    feedback: document.getElementById("feedback"),
    feedbackHeadline: document.getElementById("feedback-headline"),
    feedbackExplanation: document.getElementById("feedback-explanation"),
    btnStart: document.getElementById("btn-start"),
    btnNext: document.getElementById("btn-next"),
    btnRestart: document.getElementById("btn-restart"),
    endRankTitle: document.getElementById("end-rank-title"),
    endSummary: document.getElementById("end-summary"),
    scoreRing: document.getElementById("score-ring"),
    scoreRingText: document.getElementById("score-ring-text"),
  };

  function showScreen(name) {
    Object.values(screens).forEach((s) => s.classList.remove("screen--active"));
    screens[name].classList.add("screen--active");
  }

  async function loadQuestions() {
    const res = await fetch("/questions");
    if (!res.ok) throw new Error("Failed to load questions: " + res.status);
    questions = await res.json();
  }

  function renderQuestion() {
    const q = questions[currentIndex];

    el.hudSector.textContent = `${currentIndex + 1} / ${questions.length}`;
    el.hudScore.textContent = String(score);

    const pct = (currentIndex / questions.length) * 100;
    el.progressFill.style.width = pct + "%";
    el.progressShip.style.left = pct + "%";

    el.prompt.textContent = q.prompt;
    el.feedback.hidden = true;
    el.options.innerHTML = "";

    q.options.forEach((optionText) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "option";
      btn.textContent = optionText;
      btn.addEventListener("click", () => handleAnswer(btn, optionText, q));
      el.options.appendChild(btn);
    });
  }

  function handleAnswer(clickedBtn, chosenText, q) {
    // Lock all options so the player can't click twice
    const allOptions = el.options.querySelectorAll(".option");
    allOptions.forEach((b) => (b.disabled = true));

    const isCorrect = chosenText === q.answer;
    if (isCorrect) {
      score += 1;
      clickedBtn.classList.add("is-correct");
    } else {
      clickedBtn.classList.add("is-wrong");
      allOptions.forEach((b) => {
        if (b.textContent === q.answer) b.classList.add("is-correct");
      });
    }

    el.hudScore.textContent = String(score);

    el.feedbackHeadline.textContent = isCorrect ? "Correct! Sector cleared." : "Not quite.";
    el.feedbackHeadline.className = "feedback-headline " + (isCorrect ? "is-correct" : "is-wrong");
    el.feedbackExplanation.textContent = q.explanation || "";
    el.feedback.hidden = false;

    // Change the Next button's label on the last question
    el.btnNext.textContent =
      currentIndex === questions.length - 1 ? "See Mission Report" : "Next Transmission";
  }

  function goToNext() {
    currentIndex += 1;
    if (currentIndex >= questions.length) {
      finishGame();
      return;
    }
    renderQuestion();
  }

  function finishGame() {
    const total = questions.length;
    const pct = Math.round((score / total) * 100);

    let rank = "Cadet";
    if (pct === 100) rank = "Fleet Admiral";
    else if (pct >= 75) rank = "Commander";
    else if (pct >= 50) rank = "Pilot";
    else if (pct >= 25) rank = "Navigator Trainee";

    el.endRankTitle.textContent = rank;
    el.endSummary.textContent = `You solved ${score} of ${total} transmissions.`;
    el.scoreRing.style.setProperty("--pct", String(pct));
    el.scoreRingText.textContent = `${score}/${total}`;

    showScreen("end");
  }

  async function startGame() {
    score = 0;
    currentIndex = 0;
    try {
      await loadQuestions();
    } catch (err) {
      el.prompt.textContent = "Could not reach mission control. Please refresh and try again.";
      showScreen("question");
      return;
    }
    showScreen("question");
    renderQuestion();
  }

  el.btnStart.addEventListener("click", startGame);
  el.btnNext.addEventListener("click", goToNext);
  el.btnRestart.addEventListener("click", startGame);

  // ---------- Lightweight animated starfield background ----------
  function initStarfield() {
    const canvas = document.getElementById("starfield");
    const ctx = canvas.getContext("2d");
    let stars = [];

    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      const count = Math.floor((canvas.width * canvas.height) / 9000);
      stars = Array.from({ length: count }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: Math.random() * 2.2 + 0.6,
        a: Math.random() * 0.6 + 0.3,
        twinkleSpeed: Math.random() * 0.02 + 0.005,
      }));
    }

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (const s of stars) {
        if (!reduceMotion) {
          s.a += s.twinkleSpeed;
          if (s.a > 1 || s.a < 0.2) s.twinkleSpeed *= -1;
        }
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(124, 92, 252, ${s.a * 0.5})`;
        ctx.fill();
      }
      if (!reduceMotion) requestAnimationFrame(draw);
    }

    window.addEventListener("resize", resize);
    resize();
    draw();
  }

  initStarfield();
})();
