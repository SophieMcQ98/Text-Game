import argparse
import random
import re

from game_engine import GameConfig, GameEngine


RIDDLE_WRONG_LINES = [
    "no. listen again.",
    "not yet. the echo still hides its name.",
    "you reached too quickly. look at the ruin between the words.",
    "the traveler is still waiting. answer true.",
]

TEST_ECHOES_INPUTS = {
    "persistent_description": "my blue and pink vape",
    "persistent_meaning": "I smoke nicotine to calm my anxiety, and I have a sentimental attachment to this particular vape.",
    "persistent_loss": "I would have to buy a new vape",
    "shame_confession": "I am ashamed about eating too much",
    "lost_thing": "my ex Marty who broke up with me",
    "lost_permanence": "my ex Marty who broke up with me",
}


def run_scene(engine: GameEngine) -> None:
    state = engine.get_state()
    echoes_inputs = state.get("echoes_inputs", {})
    if engine.config.test_mode:
        echoes_inputs = TEST_ECHOES_INPUTS.copy()

    travelers = [
        {
            "name": "The Iron Pilgrim",
            "seed": (
                f"Object details: {echoes_inputs.get('persistent_description', '')}\n"
                f"Why chosen: {echoes_inputs.get('persistent_meaning', '')}\n"
                f"Cost of loss: {echoes_inputs.get('persistent_loss', '')}"
            ),
        },
        {
            "name": "The Veiled Penitent",
            "seed": f"Confession: {echoes_inputs.get('shame_confession', '')}",
        },
        {
            "name": "The Last Lantern",
            "seed": (
                f"What was lost: {echoes_inputs.get('lost_thing', '')}\n"
                f"Why permanent: {echoes_inputs.get('lost_permanence', '')}"
            ),
        },
    ]

    engine.say("echoes.")
    engine.say("three travelers came before you. you have worn each of their names.")
    engine.say("hear them. answer them. then we continue.")

    story_packets = _build_story_packets(engine, travelers)

    if engine.config.debug_mode:
        engine.say("[debug] all echoes generated upfront.")
        for i, packet in enumerate(story_packets, start=1):
            engine.say(f"[debug] traveler {i} answer: {packet['answer']}", pause_after=0.2)

    for i, packet in enumerate(story_packets, start=1):
        paragraphs = packet["paragraphs"]
        riddle = packet["riddle"]
        answer = packet["answer"]
        traveler_name = packet["name"]

        engine.say(f"traveler {i}: {traveler_name}")
        for paragraph in paragraphs:
            engine.say(paragraph)

        engine.say(riddle)
        _wait_for_riddle_answer(engine, riddle, answer)
        engine.say("good. the echo opens.")

    engine.say("three echoes answered.")
    engine.say("the old road remembers your step.")


def _build_story_packets(engine: GameEngine, travelers: list[dict[str, str]]) -> list[dict[str, object]]:
    packets: list[dict[str, object]] = []
    for traveler in travelers:
        story = _generate_traveler_story(engine, traveler["name"], traveler["seed"])
        paragraphs, riddle, answer = _parse_story_payload(story)

        if _is_default_riddle(riddle):
            riddle, answer = _generate_fallback_riddle(engine, traveler["name"], paragraphs, traveler["seed"])

        paragraphs = [_limit_to_two_sentences(p) for p in paragraphs]

        packets.append(
            {
                "name": traveler["name"],
                "paragraphs": paragraphs,
                "riddle": riddle,
                "answer": answer,
            }
        )
    return packets


def _generate_traveler_story(engine: GameEngine, traveler_name: str, seed_text: str) -> str:
    prompt = f'''Write a short medieval-themed ritual vignette for a horror text game.

Traveler name: {traveler_name}
Source details from prior scene:
{seed_text}

Requirements:
- Exactly 4 short paragraphs, 1-2 sentences each.
- Vague, ominous, and old-timey medieval tone.
- Keep language plain and poetic, similar to ritual game dialogue.
- Story should subtly reflect the source details, without naming modern context.
- After the 4 paragraphs, include one short riddle tied to the story.
- Also provide the intended riddle answer (1-4 words).

Return using this exact format:
P1: <paragraph 1>
P2: <paragraph 2>
P3: <paragraph 3>
P4: <paragraph 4>
RIDDLE: <riddle line>
ANSWER: <answer text>
'''
    return engine.generate(prompt)


def _parse_story_payload(payload: str) -> tuple[list[str], str, str]:
    rows = [row.strip() for row in payload.splitlines() if row.strip()]
    data: dict[str, str] = {}
    current_key = ""

    for row in rows:
        # Accept common label variants like "P1)", "Riddle -", "Answer"
        if ":" in row:
            key, value = row.split(":", 1)
            key_norm = _normalize_label(key)
            if key_norm in {"P1", "P2", "P3", "P4", "RIDDLE", "ANSWER"}:
                data[key_norm] = value.strip()
                current_key = key_norm
                continue

        riddle_match = re.match(r"^riddle\s*[-:]\s*(.+)$", row, flags=re.IGNORECASE)
        if riddle_match:
            data["RIDDLE"] = riddle_match.group(1).strip()
            current_key = "RIDDLE"
            continue

        answer_match = re.match(r"^answer\s*[-:]\s*(.+)$", row, flags=re.IGNORECASE)
        if answer_match:
            data["ANSWER"] = answer_match.group(1).strip()
            current_key = "ANSWER"
            continue

        # Treat unlabeled continuation lines as part of previous recognized field.
        if current_key:
            data[current_key] = f"{data[current_key]} {row}".strip()

    if "RIDDLE" not in data:
        for row in reversed(rows):
            if "?" in row:
                data["RIDDLE"] = row
                break

    p1 = data.get("P1", "he came by candle and ash, saying little.")
    p2 = data.get("P2", "the stones listened and did not answer.")
    p3 = data.get("P3", "he left a thing that could not be lifted again.")
    p4 = data.get("P4", "by dawn the bell was silent, and still he knelt.")

    riddle = data.get("RIDDLE", "Riddle: what burns without flame and follows every vow?")
    answer = data.get("ANSWER", "memory").strip().lower()

    if not riddle.lower().startswith("riddle"):
        riddle = f"Riddle: {riddle}"

    return [p1, p2, p3, p4], riddle, answer


def _normalize_label(label: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", label.upper())


def _limit_to_two_sentences(text: str) -> str:
    sentence_matches = re.findall(r"[^.!?]+[.!?]", text)
    if not sentence_matches:
        return text.strip()
    limited = " ".join(s.strip() for s in sentence_matches[:2]).strip()
    return limited if limited else text.strip()


def _is_default_riddle(riddle: str) -> bool:
    return "what burns without flame and follows every vow?" in riddle.lower()


def _generate_fallback_riddle(
    engine: GameEngine,
    traveler_name: str,
    paragraphs: list[str],
    seed_text: str,
) -> tuple[str, str]:
    prompt = f'''Create one short medieval-toned riddle and one short answer for this traveler.

Traveler: {traveler_name}
Source details:
{seed_text}

Story context:
P1: {paragraphs[0]}
P2: {paragraphs[1]}
P3: {paragraphs[2]}
P4: {paragraphs[3]}

Return exactly:
RIDDLE: <one line ending with ?>
ANSWER: <1-4 word answer>
'''
    payload = engine.generate(prompt, temperature=0.6, max_tokens=120)
    _, riddle, answer = _parse_story_payload(payload)
    return riddle, answer


def _wait_for_riddle_answer(engine: GameEngine, riddle: str, answer: str) -> None:
    while True:
        guess = engine.ask()
        if not guess:
            engine.say(random.choice(RIDDLE_WRONG_LINES))
            continue

        if _classify_riddle_guess(engine, riddle, answer, guess) == "correct":
            return

        engine.say(random.choice(RIDDLE_WRONG_LINES))


def _classify_riddle_guess(engine: GameEngine, riddle: str, answer: str, guess: str) -> str:
    prompt = f'''You are grading a riddle guess in a text game.

Riddle: "{riddle}"
Intended answer: "{answer}"
Player guess: "{guess}"

Classify as exactly one label:
- correct: guess is equivalent or clearly close in meaning to the intended answer
- incorrect: guess does not match

Respond with one label only.'''
    return engine.classify(prompt)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Echoes scene.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Use Echoes test seed inputs instead of saved Threshold inputs.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Generate all traveler stories upfront and print debug answers.",
    )
    args = parser.parse_args()

    config = GameConfig(
        player_name="Sophie",
        state_file=".threshold_progress.json",
        test_mode=args.test,
        debug_mode=args.debug,
    )
    engine = GameEngine(config)
    engine.run_scene(run_scene)


if __name__ == "__main__":
    main()
