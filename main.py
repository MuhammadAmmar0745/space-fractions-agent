"""
main.py
-------
Poora pipeline ek command se chalane ke liye.

GEMINI (free - recommended):
    export GEMINI_API_KEY=your_key_here
    python main.py

CLAUDE:
    export ANTHROPIC_API_KEY=your_key_here
    python main.py --provider anthropic

Ye 3 steps karta hai:
  1. Architecture_Documentation.md + Architecture_View.md --(parser.py)--> agent_input.json
  2. agent_input.json --(code_agent.py: plan)--> file list plan
  3. file list plan   --(code_agent.py: generate)--> game_output/ (poora project)
"""

import argparse
from agent.parser import build_agent_input_json
from agent.code_agent import CodeAgent


def main():
    ap = argparse.ArgumentParser(description="Space Fractions Code Agent - full pipeline")
    ap.add_argument("--doc", default="Architecture_Documentation.md")
    ap.add_argument("--view", default="Architecture_View.md")
    ap.add_argument("--input-json", default="agent_input.json")
    ap.add_argument("--out", default="game_output")
    ap.add_argument("--provider", default=None, choices=["gemini", "anthropic"],
                    help="LLM provider. Agar na do to environment key se khud detect ho jayega.")
    ap.add_argument("--fresh", action="store_true",
                    help="Pehle se generated files ko ignore kar ke sab kuch dobara banao (default: resume/skip).")
    args = ap.parse_args()

    print("=== Step 1/3: Parsing architecture docs into structured JSON ===")
    spec = build_agent_input_json(args.doc, args.view, args.input_json)
    comps = [c["name"] for c in spec["architecture_documentation"]["components"]]
    views = list(spec["architecture_views"].keys())
    print(f"  Components: {comps}")
    print(f"  Views: {views}")
    print(f"  -> {args.input_json} saved.\n")

    print("=== Step 2/3 & 3/3: Running Code Agent (plan + generate files) ===")
    agent = CodeAgent(provider=args.provider, output_dir=args.out)
    written = agent.run(args.input_json, resume=not args.fresh)

    print("\n=== DONE ===")
    print(f"Generated {len(written)} files in ./{args.out}/")
    print(f"Ab chalao:  cd {args.out} && pip install -r requirements.txt && python app.py")


if __name__ == "__main__":
    main()
