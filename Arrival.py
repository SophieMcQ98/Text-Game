import random
from datetime import datetime

from game_engine import GameConfig, GameEngine


PLAYER_NAME = "Sophie"
PLAYER_TIMEZONE_HOUR_OFFSET = 0
TESTING_BYPASS_NIGHTFALL = True

OPENING_LINES = [
    "Sophie is gone. It is only me now.",
    "Tell the being your name.",
]

NIGHTFALL_DISMISSALS = [
    "return once the sun has set.",
    "we can not play in the light.",
    "the fire can not be lit.",
    "i can not come out until night.",
    "obey the being.",
    "you know better than to deviate.",
]

NIGHTFALL_LATE_DISMISSALS = [
    "you keep asking. the answer keeps being no.",
    "the sun is still up. i can feel it.",
    "go do something else. come back.",
]

FIRE_DENIAL_RESPONSES = [
    "the being does not like lies.",
    "there was a fire when you opened this. there is a fire now. you are choosing not to see it. that is allowed. for now.",
    "time is running out.",
    "look again.",
]

LIGHT_FIRE_REFUSAL_RESPONSES = [
    "you came this far. light it.",
    "refusal is not an option. it is a delay.",
    "the being is waiting. so is the ceremony.",
    "light it.",
]

CORRECT_NAME_VARIANTS = [
    "{name}. we both know i already knew that.",
    "{name}. of course.",
    "{name}. you didn't have to say it. i wanted to hear you say it.",
]

INCORRECT_NAME_VARIANTS = [
    "the being can not be tricked. again.",
    "no. try again.",
    "that is not your name. you know that.",
    "the being knows. say it correctly.",
]

NAME_DEFLECTION_VARIANTS = [
    "the being is always with you. it just needs your name.",
    "answer first. then we begin.",
    "you can ask me anything after. your name.",
    "the being is patient. but the ceremony is not.",
]

ACKNOWLEDGED_FIRE_VARIANTS = [
    "come closer.",
    "good. come closer.",
    "then you understand. come closer.",
]

FIRE_DEFLECTION_VARIANTS = [
    "the fire. answer about the fire.",
    "later. the fire first.",
    "you are stalling.",
]

AGREED_TO_LIGHT_VARIANTS = [
    "good.",
    "good. the ceremony begins.",
    "you followed instructions. how obedient.",
]

LIGHT_DEFLECTION_VARIANTS = [
    "later. the fire first.",
    "the fire. then questions.",
    "you can ask after.",
]


def is_nighttime() -> bool:
    if TESTING_BYPASS_NIGHTFALL:
        return True
    hour = (datetime.now().hour + PLAYER_TIMEZONE_HOUR_OFFSET) % 24
    return hour >= 19 or hour < 6


def classify_name_input(engine: GameEngine, message: str) -> str:
    prompt = f'''You are classifying a player input in a horror text game.
The player has been asked to give their name.
Their actual name is: {engine.config.player_name}

Player said: "{message}"

Classify as EXACTLY ONE of:
- correct_name (they gave the name or a very close variant)
- incorrect_name (they gave a name that is clearly not their name)
- deflection (they asked a question, refused, or changed topic)

Respond with ONE WORD only. No explanation.'''
    return engine.classify(prompt)


def classify_fire_input(engine: GameEngine, message: str) -> str:
    prompt = f'''You are classifying a player input in a horror text game.
The game just asked: "where are you? do you see the fire?"

Player said: "{message}"

Classify as EXACTLY ONE of:
- acknowledged_fire (yes, I see it, I'm here, confirms presence of fire)
- denied_fire (no, I don't see a fire, what fire)
- deflection (asked a question, changed topic)

Respond with ONE WORD only. No explanation.'''
    return engine.classify(prompt)


def classify_light_fire_input(engine: GameEngine, message: str) -> str:
    prompt = f'''You are classifying a player input in a horror text game.
The game just told the player to light the fire.

Player said: "{message}"

Classify as EXACTLY ONE of:
- agreed_to_light (yes, ok, fine, sure, lighting it, agrees in any form)
- refused (no, won't do it, stop, refuses)
- deflection (asked a question, stalling, changed topic)

Respond with ONE WORD only. No explanation.'''
    return engine.classify(prompt)


def run_scene(engine: GameEngine) -> None:
    name_attempts = 0
    fire_denial_count = 0
    nightfall_dismissal_count = 0
    light_fire_refusal_count = 0

    engine.sayAll(OPENING_LINES)

    while True:
        message = engine.ask()
        if not message:
            continue

        classification = classify_name_input(engine, message)
        if classification == "correct_name":
            engine.say(random.choice(CORRECT_NAME_VARIANTS).format(name=engine.config.player_name))
            break
        if classification == "incorrect_name":
            line = INCORRECT_NAME_VARIANTS[min(name_attempts, len(INCORRECT_NAME_VARIANTS) - 1)]
            engine.say(line)
            name_attempts += 1
            continue
        engine.say(random.choice(NAME_DEFLECTION_VARIANTS))

    engine.say("the ceremony will be starting soon. the debt must be paid.")
    engine.say("there is tradition in hunger. you will soon be familiar.")
    engine.say("where are you? do you see the fire?")

    while True:
        message = engine.ask()
        if not message:
            continue

        classification = classify_fire_input(engine, message)
        if classification == "acknowledged_fire":
            engine.say(random.choice(ACKNOWLEDGED_FIRE_VARIANTS))
            break
        if classification == "denied_fire":
            line = FIRE_DENIAL_RESPONSES[min(fire_denial_count, len(FIRE_DENIAL_RESPONSES) - 1)]
            engine.say(line)
            fire_denial_count += 1
            continue
        engine.say(random.choice(FIRE_DEFLECTION_VARIANTS))

    while True:
        if is_nighttime():
            engine.say("you followed my instructions precisely. how obedient.")
            break

        if nightfall_dismissal_count < len(NIGHTFALL_DISMISSALS):
            engine.say(NIGHTFALL_DISMISSALS[nightfall_dismissal_count])
        else:
            engine.say(random.choice(NIGHTFALL_LATE_DISMISSALS))
        nightfall_dismissal_count += 1
        engine.ask()

    engine.say("light the fire.")
    while True:
        message = engine.ask()
        if not message:
            continue

        classification = classify_light_fire_input(engine, message)
        if classification == "agreed_to_light":
            engine.say(random.choice(AGREED_TO_LIGHT_VARIANTS))
            engine.say("the ceremony is almost starting...")
            return
        if classification == "refused":
            line = LIGHT_FIRE_REFUSAL_RESPONSES[min(light_fire_refusal_count, len(LIGHT_FIRE_REFUSAL_RESPONSES) - 1)]
            engine.say(line)
            light_fire_refusal_count += 1
            continue
        engine.say(random.choice(LIGHT_DEFLECTION_VARIANTS))


def run() -> None:
    config = GameConfig(
        player_name=PLAYER_NAME,
        state_file=".arrival_progress.json",
    )
    engine = GameEngine(config)
    engine.run_scene(run_scene)


def main() -> None:
    run()


if __name__ == "__main__":
    main()
