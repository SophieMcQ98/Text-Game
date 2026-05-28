import json
import os
import random
import select
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable

from openai import OpenAI


@dataclass
class GameConfig:
    player_name: str = "Sophie"
    state_file: str = ".arrival_progress.json"
    test_mode: bool = False
    debug_mode: bool = False
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "llama3.1:8b"


class GameEngine:
    def __init__(self, config: GameConfig):
        self.config = config
        self._state = self._load_state()
        self._llm = OpenAI(base_url=config.llm_base_url, api_key=config.llm_api_key)

    def say(self, text: str, pause_after: float = 2.0) -> None:
        print(f"\n{text}")
        if pause_after > 0:
            time.sleep(pause_after)
    
    def sayAll(self, texts: list[str], pause_after_each: float = 2.0) -> None:
        for text in texts:
            self.say(text, pause_after=pause_after_each)

    def pause(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)

    def pause_between(self, low_seconds: float, high_seconds: float) -> None:
        time.sleep(random.uniform(low_seconds, high_seconds))

    def ask(self, prompt: str = "> ") -> str:
        try:
            return input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    def wait_for_message_window(
        self,
        open_after_seconds: float,
        window_seconds: float,
        fail_after_seconds: float,
    ) -> str | None:
        start = time.monotonic()
        print("\n> ", end="", flush=True)

        while True:
            elapsed = time.monotonic() - start
            if elapsed >= fail_after_seconds:
                print()
                return None

            timeout = min(0.25, fail_after_seconds - elapsed)
            ready, _, _ = select.select([sys.stdin], [], [], timeout)
            if not ready:
                continue

            raw = sys.stdin.readline()
            if raw == "":
                print()
                return None

            message = raw.strip()
            message_elapsed = time.monotonic() - start

            if open_after_seconds <= message_elapsed <= (open_after_seconds + window_seconds):
                return message

            # Messages outside the window are intentionally ignored.
            print("> ", end="", flush=True)

    def run_scene(self, runner: Callable[["GameEngine"], None]) -> None:
        runner(self)

    def classify(self, prompt: str) -> str:
        response = self._llm.chat.completions.create(
            model=self.config.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=12,
        )
        return response.choices[0].message.content.strip().lower().split()[0]

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 700) -> str:
        response = self._llm.chat.completions.create(
            model=self.config.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    def get_state(self) -> dict[str, Any]:
        return self._state

    def save_state(self) -> None:
        with open(self.config.state_file, "w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2)

    @staticmethod
    def iso_to_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value)

    @staticmethod
    def datetime_to_iso(value: datetime | None) -> str | None:
        if not value:
            return None
        return value.isoformat()

    @staticmethod
    def next_sundown(now: datetime, hour: int = 19) -> datetime:
        target = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return target

    def _load_state(self) -> dict[str, Any]:
        if not os.path.exists(self.config.state_file):
            return {"miss_count": 0, "lock_until": None}

        try:
            with open(self.config.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "miss_count" not in data:
                data["miss_count"] = 0
            if "lock_until" not in data:
                data["lock_until"] = None
            return data
        except (json.JSONDecodeError, OSError):
            return {"miss_count": 0, "lock_until": None}
