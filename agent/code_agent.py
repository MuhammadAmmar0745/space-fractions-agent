"""
code_agent.py
-------------
Ye humara asal "Code Agent" hai - Claude Code se inspire hoke banaya gaya
(dekho: anthropics/claude-code, Windy3f3f3f3f/how-claude-code-works).

Ye kaise kaam karta hai (bachon wali zubaan mein):

  1. PARHNA (Read)   -> agent_input.json (parser.py se bana hua) parhta hai.
  2. SOCHNA (Plan)    -> LLM ko is JSON ke sath bolta hai: "in requirements se
                          project files ki list banao" (jaise ek insaan
                          programmer pehle plan banata hai).
  3. LIKHNA (Act)     -> Har file ke liye LLM ko bolta hai "ab is file ka
                          poora code likho", aur wo code disk par save
                          kar deta hai. Ye "tool use" jaisa hai - Claude Code
                          bhi files parhne/likhne ke liye tools call karta hai,
                          hum bhi wahi pattern chotay scale par follow kar
                          rahe hain.
  4. DOHRANA (Loop)   -> Har file ke liye step 3 dohrata hai jab tak poora
                          project ban na jaye.

Is se ye "agentic" ban jata hai: ye sirf ek prompt se ek jawab nahi deta,
balke KHUD decide karta hai ke kaunsi files chahiye aur unhe ek-ek karke
banata hai - bilkul waisay jaise ek asal AI coding agent kaam karta hai.

Provider-independent hai: Gemini ya Claude, dono ke sath chalta hai.
"""

import json
import re
import time
from pathlib import Path

from agent.llm_provider import get_provider, auto_detect_provider


def _strip_fences(text: str | None) -> str:
    """LLM aksar ```json ya ```python fences laga deta hai - unhe hata deta hai.

    Kabhi kabhi (khaas kar bohot chhoti files jaise __init__.py ke liye) LLM
    khali response de deta hai - us case mein crash hone ki bajaye khali
    string return karte hain.
    """
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z0-9]*\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


class CodeAgent:
    def __init__(self, provider: str | None = None, output_dir: str = "game_output", verbose: bool = True):
        provider = provider or auto_detect_provider()
        self.provider_name = provider
        self.llm = get_provider(provider)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose

    def _log(self, msg: str):
        if self.verbose:
            print(msg, flush=True)

    def _call_llm(self, prompt: str, max_tokens: int, retries: int = 2) -> str:
        """LLM call with limited retry.

        NOTE: har retry khud bhi ek API request hai, is liye free-tier quota
        par retries ki tadaad jaan-boojh kar kam rakhi hai (zyada retries ka
        matlab quota jaldi khatam hona).
        """
        for attempt in range(retries):
            try:
                return self.llm.complete(prompt, max_tokens=max_tokens)
            except Exception as e:
                msg = str(e)
                if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                    # Quota/rate-limit hit - lamba wait zaroori hai, chota nahi
                    wait = 20
                else:
                    wait = 2 ** attempt * 3
                if attempt == retries - 1:
                    raise
                self._log(f"  [retry] {type(e).__name__} -- {wait}s baad dobara koshish...")
                time.sleep(wait)

    # ---------- STEP 2: SOCHNA (Plan) ----------
    def plan_file_list(self, spec: dict) -> list[dict]:
        """LLM se poochta hai: 'is architecture se kaunsi files banani chahiye?'"""
        prompt = f"""You are a senior software architect turning an architecture spec into a
concrete project file plan.

Here is the parsed architecture specification (JSON):
{json.dumps(spec, indent=2)[:6000]}

Task: Produce the list of files needed to implement a working, runnable web app
for this "Space Fractions" learning game, PLUS supporting project files.

Required categories (include all that apply):
  - Frontend game files (HTML/CSS/JS) implementing: intro screen, main menu,
    a series of fraction questions, and an ending/score screen with feedback.
  - A small Flask backend serving question data via a REST API
    (matching the openapi contract in the spec where sensible).
  - A question data file (JSON) with real fraction questions for 6th graders.
  - requirements.txt (Python deps)
  - README.md
  - Dockerfile
  - At least one pytest test file testing core game logic
    (e.g. fraction answer-checking and scoring).

Respond with ONLY a JSON array. No prose, no markdown fences. Each item:
{{"path": "relative/file/path.ext", "purpose": "one sentence description of what this file must contain/do"}}

Keep the list focused: 8-14 files total is ideal for a small but complete project.
Put the frontend at static/index.html (served by Flask) or index.html at root."""

        raw = self._call_llm(prompt, max_tokens=2500)
        cleaned = _strip_fences(raw)
        try:
            plan = json.loads(cleaned)
        except json.JSONDecodeError:
            # Kabhi kabhi LLM prose ke sath JSON deta hai - array nikalne ki koshish
            match = re.search(r"\[.*\]", cleaned, re.DOTALL)
            if not match:
                raise ValueError(f"Plan JSON parse nahi ho saka. LLM ne ye diya:\n{cleaned[:500]}")
            plan = json.loads(match.group(0))

        # Validate
        plan = [p for p in plan if isinstance(p, dict) and "path" in p]
        if not plan:
            raise ValueError("Plan khali hai - LLM ne koi valid file entry nahi di.")
        return plan

    # ---------- STEP 3: LIKHNA (Act) ----------
    def generate_file(self, spec: dict, file_plan: dict, already_written: list[str]) -> str:
        """Ek single file ka poora content generate karta hai."""
        prompt = f"""You are implementing part of a project based on this architecture spec:
{json.dumps(spec, indent=2)[:4000]}

Files already created in this project: {already_written}

Now write the COMPLETE content for this file:
  Path: {file_plan['path']}
  Purpose: {file_plan.get('purpose', 'implement this file')}

Rules:
- Output ONLY the raw file content. No markdown fences, no explanation before/after.
- The file must be complete and syntactically valid on its own.
- Keep it simple, readable, and actually functional. NO TODO placeholders for
  core logic - implement real fraction question logic, real UI, real styling.
- If this is an HTML file, include inline <style> and <script> so it runs in a
  browser, and make the UI colourful and space-themed (it's for 6th graders).
- Make sure filenames/imports are consistent with the files already created."""

        raw = self._call_llm(prompt, max_tokens=8000)
        return _strip_fences(raw)

    # ---------- STEP 4: DOHRANA (Loop) ----------
    def run(self, spec_json_path: str, resume: bool = True):
        spec = json.loads(Path(spec_json_path).read_text(encoding="utf-8"))

        self._log(f"[agent] Provider: {self.provider_name}")

        # Agar pehle se plan save hai (pichli run se), wahi use karo -
        # taake plan_file_list() dobara call na ho (quota bachao)
        plan_cache = self.output_dir / ".agent_plan.json"
        if resume and plan_cache.is_file():
            self._log("[agent] Purana plan mil gaya, dobara plan nahi banaya ja raha (quota save)...")
            file_plan = json.loads(plan_cache.read_text(encoding="utf-8"))
        else:
            self._log("[agent] Step 1 - Planning file list...")
            file_plan = self.plan_file_list(spec)
            plan_cache.write_text(json.dumps(file_plan, indent=2), encoding="utf-8")

        self._log(f"[agent] Plan ready: {len(file_plan)} files")
        for p in file_plan:
            self._log(f"         - {p['path']}")

        self._log("\n[agent] Step 2 - Generating files...")
        written = []
        skipped = []
        for i, item in enumerate(file_plan, 1):
            path = self.output_dir / item["path"]

            if resume and path.is_file() and path.stat().st_size > 0:
                self._log(f"  [{i}/{len(file_plan)}] {item['path']} -- pehle se maujood hai, skip.")
                written.append(item["path"])
                skipped.append(item["path"])
                continue

            self._log(f"  [{i}/{len(file_plan)}] {item['path']} ...")
            try:
                content = self.generate_file(spec, item, written)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                written.append(item["path"])
            except Exception as e:
                self._log(f"      !! FAILED: {type(e).__name__}: {e}")

        remaining = [p["path"] for p in file_plan if p["path"] not in written]
        self._log(f"\n[agent] Done. {len(written)}/{len(file_plan)} files written "
                   f"({len(skipped)} skipped as already-existing) to {self.output_dir}/")
        if remaining:
            self._log(f"[agent] Abhi baqi hain: {remaining}")
            self._log("[agent] Kuch der (quota reset hone tak) intezaar kar ke 'python main.py' dobara chalayein - "
                       "ye sirf baqi files banayega, pehli wali dobara nahi banega.")
        return written


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Run the Code Agent to generate the Space Fractions project.")
    ap.add_argument("--input", default="agent_input.json", help="Parsed architecture JSON (from parser.py)")
    ap.add_argument("--out", default="game_output", help="Output project directory")
    ap.add_argument("--provider", default=None, choices=["gemini", "anthropic"], help="LLM provider (auto-detect if omitted)")
    args = ap.parse_args()

    agent = CodeAgent(provider=args.provider, output_dir=args.out)
    agent.run(args.input)
