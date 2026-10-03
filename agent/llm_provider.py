"""
llm_provider.py
---------------
Ye ek chota sa "adapter" hai jo alag alag LLM providers ko ek hi
interface ke peechay chhupa deta hai.

Kyun? Taake humara Code Agent kisi ek company se bandha na ho.
Aap Google Gemini (free tier) ya Anthropic Claude, jo bhi available ho,
use kar saken - agent ka baqi code bilkul same rahega.

Use:
    llm = get_provider("gemini")      # ya "anthropic"
    text = llm.complete("your prompt here", max_tokens=2000)
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path


def _load_dotenv():
    """
    Project folder ki .env file parh kar keys ko environment mein daal deta hai.

    Is se user ko terminal mein 'export'/'set' likhne ki zaroorat nahi -
    wo bas .env file mein key paste kar deta hai aur kaam ho jata hai.

    (Ye deliberately hand-written hai taake extra dependency na lage.)
    """
    for candidate in (Path.cwd() / ".env", Path(__file__).resolve().parent.parent / ".env"):
        if not candidate.is_file():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            # Pehle se set environment variable ko override nahi karte
            if key and value and key not in os.environ:
                os.environ[key] = value
        break


_load_dotenv()


class LLMProvider(ABC):
    """Base class - har provider ko sirf complete() implement karna hai."""

    @abstractmethod
    def complete(self, prompt: str, max_tokens: int = 2000) -> str:
        """Prompt bhejo, plain text jawab wapas lo."""
        ...


class GeminiProvider(LLMProvider):
    """Google Gemini - free API key: https://aistudio.google.com/apikey

    Google retires/renames Gemini model IDs frequently. Instead of hardcoding
    one model name (which breaks every time Google ships a new generation),
    this tries a list of candidates in order and sticks with the first one
    that actually works - self-healing against renames/retirements.
    """

    # Priority order: newest small/cheap models first (best free-tier quota),
    # older ones as fallback in case an account only has access to those.
    CANDIDATE_MODELS = [
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-2.5-flash",
        "gemini-2.0-flash-lite",
    ]

    def __init__(self, api_key: str | None = None, model: str | None = None):
        try:
            from google import genai
        except ImportError as e:
            raise ImportError(
                "Gemini SDK nahi mila. Chalao: pip install google-genai"
            ) from e

        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ValueError(
                "GEMINI_API_KEY set nahi hai. Terminal mein chalao:\n"
                "  export GEMINI_API_KEY=your_key_here"
            )
        self.client = genai.Client(api_key=key)
        # Agar user ne specific model diya hai to usay list ke sabse aagay rakho
        self.candidates = [model] + [m for m in self.CANDIDATE_MODELS if m != model] if model else list(self.CANDIDATE_MODELS)
        self.model = self.candidates[0]  # display/log ke liye - complete() ise update kar dega

    def complete(self, prompt: str, max_tokens: int = 2000) -> str:
        from google.genai import types

        # Jo model pichli baar kaam kar chuka hai, usay list ke sabse aagay rakho
        # taake har call par purane 404 candidates dobara try na karne padein.
        ordered = [self.model] + [m for m in self.candidates if m != self.model]

        last_error = None
        for candidate in ordered:
            try:
                resp = self.client.models.generate_content(
                    model=candidate,
                    contents=prompt,
                    config=types.GenerateContentConfig(max_output_tokens=max_tokens),
                )
                if self.model != candidate:
                    print(f"[gemini] '{self.model}' available nahi tha, '{candidate}' use ho raha hai.")
                self.model = candidate  # is model ne kaam kiya - agli calls seedha isse shuru hongi
                return resp.text or ""
            except Exception as e:
                msg = str(e)
                if "NOT_FOUND" in msg or "404" in msg:
                    last_error = e
                    continue  # agla candidate try karo
                raise  # koi aur error (quota, network) - upar retry logic handle karega

        raise RuntimeError(
            f"Koi bhi Gemini model available nahi hai in mein se: {self.candidates}. "
            f"Aakhri error: {last_error}\n"
            f"Google AI Studio (aistudio.google.com) check karein ke aapki key se kaunse models active hain."
        )


class AnthropicProvider(LLMProvider):
    """Anthropic Claude - API key: https://console.anthropic.com"""

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-6"):
        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise ImportError(
                "Anthropic SDK nahi mila. Chalao: pip install anthropic"
            ) from e

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError(
                "ANTHROPIC_API_KEY set nahi hai. Terminal mein chalao:\n"
                "  export ANTHROPIC_API_KEY=your_key_here"
            )
        self.client = Anthropic(api_key=key)
        self.model = model

    def complete(self, prompt: str, max_tokens: int = 2000) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text


def get_provider(name: str = "gemini", **kwargs) -> LLMProvider:
    """Factory: naam se sahi provider bana kar deta hai."""
    name = (name or "gemini").lower()
    if name == "gemini":
        return GeminiProvider(**kwargs)
    if name in ("anthropic", "claude"):
        return AnthropicProvider(**kwargs)
    raise ValueError(f"Unknown provider: {name}. Use 'gemini' ya 'anthropic'.")


def auto_detect_provider() -> str:
    """Environment mein jo key mili hai uske hisaab se provider chun leta hai."""
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    raise ValueError(
        "\n"
        "=========================================================\n"
        "  Koi API key nahi mili.\n"
        "=========================================================\n"
        "\n"
        "  ASAAN TAREEQA (.env file):\n"
        "    1. Project folder mein '.env.example' file ka naam\n"
        "       badal kar sirf '.env' kar dein\n"
        "    2. Us file mein apni key paste karein:\n"
        "         GEMINI_API_KEY=your_key_here\n"
        "    3. Save karein aur dobara 'python main.py' chalayein\n"
        "\n"
        "  Free Gemini key yahan se milti hai:\n"
        "    https://aistudio.google.com/apikey\n"
        "\n"
        "  (Ya phir terminal mein: export GEMINI_API_KEY=...)\n"
        "=========================================================\n"
    )
