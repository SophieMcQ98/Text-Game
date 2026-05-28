import random

from game_engine import GameEngine


CONFIRMATION_RETRY_LINES = [
    "we require your yes.",
    "...we are waiting.",
    "the being does not have time. confirm.",
    "we have asked. confirm.",
    "...still waiting.",
    "the being asked once. confirm.",
    "we do not move without your yes.",
    "...we remain.",
    "the being grows impatient. confirm.",
    "we need the word. say it.",
]

APOLOGY_RETRY_LINES = [
    "say it. repent.",
    "the being is waiting for your apology.",
    "we do not proceed without it. repent."
]

BEG_RETRY_LINES = [
    "beg for forgiveness. on your knees.",
    "debase yourself. atone.",
    "there is no mercy without humiliation.",
]


def classify_confirmation(engine: GameEngine, message: str) -> str:
    prompt = f'''You are classifying a player reply in a ritual horror game.
The game is waiting for explicit confirmation to continue.

Player reply: "{message}"

Classify as exactly one label:
- confirmed: the player clearly confirms yes, says they have it, says continue, agrees, or gives explicit assent
- not_confirmed: anything else, including uncertainty, refusal, unrelated text, or vague responses

Respond with one label only.'''
    return engine.classify(prompt)


def classify_apology(engine: GameEngine, message: str) -> str:
    prompt = f'''You are classifying a player reply in a ritual horror game.
The player was told to apologize for being late.

Player reply: "{message}"

Classify as exactly one label:
- apologized: the player clearly apologizes (for example: sorry, I apologize, forgive me)
- not_apologized: anything else, including excuses, deflection, refusal, or unrelated text

Respond with one label only.'''
    return engine.classify(prompt)


def classify_beg_for_forgiveness(engine: GameEngine, message: str) -> str:
    prompt = f'''You are classifying a player reply in a ritual horror game.
The player was told to beg for forgiveness.

Player reply: "{message}"

Classify as exactly one label:
- begged: the player clearly begs or pleads for forgiveness/mercy/release
- not_begged: anything else, including neutral apology, deflection, refusal, or unrelated text

Respond with one label only.'''
    return engine.classify(prompt)


def wait_for_confirmation(engine: GameEngine) -> str:
    while True:
        message = engine.ask()
        if classify_confirmation(engine, message) == "confirmed":
            return message
        engine.say(random.choice(CONFIRMATION_RETRY_LINES))


def wait_for_apology(engine: GameEngine) -> str:
    while True:
        message = engine.ask()
        if classify_apology(engine, message) == "apologized":
            return message
        engine.say(random.choice(APOLOGY_RETRY_LINES))


def wait_for_beg_for_forgiveness(engine: GameEngine) -> str:
    while True:
        message = engine.ask()
        if classify_beg_for_forgiveness(engine, message) == "begged":
            return message
        engine.say(random.choice(BEG_RETRY_LINES))
