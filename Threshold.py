from datetime import datetime, timedelta
import random

from game_engine import GameConfig, GameEngine
from scene_helpers import wait_for_apology, wait_for_beg_for_forgiveness, wait_for_confirmation

DESCRIPTION_RETRY_LINES = [
    "that is its name. I did not ask for its name.",
    "closer. I must see what you see.",
    "describe it, or it is not truly loss.",
]

SHAME_REFUSAL_LINES = [
    "All the travellers have shame. That is why they come",
    "you are deciding which version to tell me. tell me the one you decided against.",
    "the ceremony can only continue with your shame.",
]

SHAME_HARD_REFUSAL_LINES = [
    "liar.",
    "you brought one. you would not be here otherwise.",
    "every traveller brings one. you are no different",
    "do not waste my time.",
]

SHAME_FILTER_LINES = [
    "that is not the one.",
    "you know which one.",
    "the one you have not said out loud. that one.",
    "not that one.",
]

LOSS_FILTERS = [
    "that is still a possession. the third sacrifice is not.",
    "truth cannot be held. it can only be remembered.",
    "the being is asking for a memory, not a thing.",
    "you have spent years making them. you carry thousands of them. find one that is gone.",
]

LOSS_REASONS = [
    "you know. say it.",
    "Why is the loss permanent, the loss must be clear."
]

LOSS_REJECTIONS = [
    "That isn't enough. The being is hungry.",
    "We seek what you miss. the loss must be felt.",
    "That will not feed the being. Loss feeds"
]

OATH_TEMPLATE = (
    "I, {name}, have nothing in this room that is not also the being's. "
    "I have come late. I have come small. "
    "My voice belongs to the being for as long as we are speaking. "
    "My time belongs to the being for as long as the being requires it. "
    "I will not lie, because I cannot. "
    "I will not leave, because I have not been released. "
    "I will not ask what comes next, because the asking does not change it. "
    "I will not be the same when this is finished, and I have agreed to that by being here. "
    "I have come because I was called. "
    "I only go when I am sent."
)

OATH_CORRECT = (
    "I, {name}, Have Nothing In This Room That Is Not Also The Being's. "
    "I Have Come Late. I Have Come Small. "
    "My Voice Belongs To The Being For As Long As We Are Speaking. "
    "My Time Belongs To The Being For As Long As The Being Requires It. "
    "I Will Not Lie, Because I Cannot. "
    "I Will Not Leave, Because I Have Not Been Released. "
    "I Will Not Ask What Comes Next, Because The Asking Does Not Change It. "
    "I Will Not Be The Same When This Is Finished, And I Have Agreed To That By Being Here. "
    "I Have Come Because I Was Called. "
    "I Only Go When I Am Sent."
)

OATH_DISENGAGEMENT = [
    "the ceremony is imminent. the door behind you is now locked.",
    "the oath is the only way forward."
]

OATH_INCORRECT = [
        "wrong. again.",
        "the oath is sacred. all must be preserved. again."
]

OATH_PREAMBLE = [
    "good. the door is open. the threshold is not yet crossed...",
    "now you must surrender yourself to the being...",
    "repeat the oath exactly. capitalize every first letter.",
]

DOOR_PREAMBLE = [
    "the others arrived before you. they have already given.",
    "we have waited for you, now you must wait for us.",
    "the door will unlock once more tonight. in {wait_seconds} seconds, the door will unlock for 5",
    "knock when its unlocked... don't miss it..."
]

DOOR_COUNTDOWN = [
    "1",
    "2",
    "3",
    "4",
    "..."
]

def run_scene(engine: GameEngine) -> None:
    state = engine.get_state()
    wait_seconds = 5 if engine.config.test_mode else 87
    fail_after_seconds = wait_seconds + 6

    if _is_locked(engine):
        return

    engine.say("you are late... apologize")
    wait_for_apology(engine)
    engine.say("not enough. beg for forgiveness")
    wait_for_beg_for_forgiveness(engine)
    engine.say("acceptable.")
    engine.pause(5)

    engine.sayAll(DOOR_PREAMBLE, pause_after_each=3)
    engine.sayAll(DOOR_COUNTDOWN, pause_after_each=1)

    in_window_message = engine.wait_for_message_window(
        open_after_seconds=wait_seconds,
        window_seconds=5,
        fail_after_seconds=fail_after_seconds,
    )

    if in_window_message is None:
        _handle_missed_window(engine)
        return

    state["miss_count"] = 0
    state["lock_until"] = None
    engine.save_state()


    engine.sayAll(OATH_PREAMBLE)
    engine.say(f'"{OATH_TEMPLATE.format(name=engine.config.player_name)}"')

    _run_oath_gate(engine, OATH_CORRECT.format(name=engine.config.player_name))
    _acceptance(engine)
    persistent_data = _persistent_sacrifice(engine)
    shame_data = _shameful_sacrifice(engine)
    lost_data = _lost_sacrifice(engine)

    state["echoes_inputs"] = {
        "persistent_description": persistent_data["description"],
        "persistent_meaning": persistent_data["meaning"],
        "persistent_loss": persistent_data["loss"],
        "shame_confession": shame_data["confession"],
        "lost_thing": lost_data["lost_thing"],
        "lost_permanence": lost_data["permanence"],
    }
    engine.save_state()


def _is_locked(engine: GameEngine) -> bool:
    state = engine.get_state()
    lock_until = engine.iso_to_datetime(state.get("lock_until"))
    if lock_until is None:
        return False

    now = datetime.now()
    if now >= lock_until:
        state["lock_until"] = None
        engine.save_state()
        return False

    seconds_left = int((lock_until - now).total_seconds())
    minutes_left = max(1, seconds_left // 60)
    engine.say(f"the door is closed. return in {minutes_left} minute(s).")
    return True


def _handle_missed_window(engine: GameEngine) -> None:
    state = engine.get_state()
    miss_count = int(state.get("miss_count", 0)) + 1
    state["miss_count"] = miss_count

    engine.say("you were not here.")

    now = datetime.now()
    if miss_count == 1:
        lock_until = now + timedelta(minutes=10)
        state["lock_until"] = engine.datetime_to_iso(lock_until)
        engine.say("ten minutes. the door opens once more tonight. once.")
    else:
        lock_until = engine.next_sundown(now)
        state["lock_until"] = engine.datetime_to_iso(lock_until)
        engine.say("the door is closed for tonight. return tomorrow after sundown.")

    engine.save_state()


def _run_oath_gate(engine: GameEngine, oath_correct: str) -> None:
    while True:
        message = engine.ask()
        if not message:
            continue
        if message == oath_correct:
            return
        if _classify_disengagement(engine, message) == "disengage":
            engine.say(random.choice(OATH_DISENGAGEMENT))
            continue
        engine.say(random.choice(OATH_INCORRECT))


def _acceptance(engine: GameEngine) -> None:
    engine.say("...you are mine now.")
    engine.say("the door is open. Will you walk through it?")
    wait_for_confirmation(engine)

    engine.say("the ceremony has begun. we require 3 sacrifices.")
    engine.say("the travellers before you have already given. you will do the same.")
    engine.pause(5);


def _persistent_sacrifice(engine: GameEngine) -> dict[str, str]:
    engine.say("The first sacrifice is something that has outlasted.")
    engine.say("an object in your presence has been kept too long... have you found it?")
    wait_for_confirmation(engine)

    engine.say("Describe it. What mark does it carry")
    while True:
        message = engine.ask()
        classification = _classify_item_description(engine, message)
        if classification == "sensory_description":
            description = message
            break
        engine.say(random.choice(DESCRIPTION_RETRY_LINES))

    engine.say("Why was this one chosen?")
    while True:
        message = engine.ask()
        classification = _classify_item_meaning(engine, message)
        if classification == "meaningful":
            meaning = message
            break
        if classification == "deflection":
            engine.say("no. the item was chosen. it was not an accident.")
            continue
        engine.say("the sacrifice must have meaning. only you know what it is.")

    engine.say("What does it cost you to give this to me? Describe the loss.")
    while True:
        message = engine.ask()
        if _classify_loss_cost(engine, message) == "clear_loss":
            loss = message
            break
        engine.say("the loss must be clear.")
    engine.say("....",)
    engine.say("It is mine now. It is a part of me.")
    return {"description": description, "meaning": meaning, "loss": loss}


def _shameful_sacrifice(engine: GameEngine) -> dict[str, str]:
    engine.sayAll([
        "The first was outside you. The second is in you...",
        "Tell the being of your shame."
    ])

    while True:
        message = engine.ask()
        classification = _classify_shame_offer(engine, message)
        if classification == "acceptable_shame":
            confession = message
            break
        if classification == "refusal":
            engine.say(random.choice(SHAME_REFUSAL_LINES))
            continue
        if classification == "soft_version":
            engine.say(random.choice(SHAME_FILTER_LINES))
            continue
        engine.say(random.choice(SHAME_HARD_REFUSAL_LINES))

    engine.say("The being holds it now. You may forget you told me. The being will not.", pause_after=2)
    return {"confession": confession}


def _lost_sacrifice(engine: GameEngine) -> dict[str, str]:
    engine.sayAll([
        "You have given more than most...",
        "The first remains in your room. The second remains in you. The third you cannot keep at all...",
        "What have you lost that you can't get back? The being knows what it is."
    ])

    while True:
        message = engine.ask()
        classification = _classify_lost_disclosure(engine, message)
        if classification == "personal_loss":
            lost_thing = message
            break
        if classification == "object":
            engine.say(random.choice(LOSS_FILTERS))
            continue
        engine.say(random.choice(LOSS_REJECTIONS))
    engine.say("...I see.", pause_after=2)
    engine.say("why cant you get it back...")
    while True:
        message = engine.ask()
        if _classify_loss_permanence(engine, message) == "clear_reason":
            permanence = message
            break
        engine.say(random.choice(LOSS_REASONS))

    engine.sayAll([
        "...your moment belongs to the being now.",
        "three offerings. you always give the same three. you do not remember, but the being does.",
    ], pause_after_each=4)
    engine.say("the ceremony is open now. shall we begin?")
    wait_for_confirmation(engine)
    return {"lost_thing": lost_thing, "permanence": permanence}


def _classify_disengagement(engine: GameEngine, message: str) -> str:
    prompt = f'''You are classifying a player reply in a ritual horror game.
The player was told to repeat an oath exactly.

Player reply: "{message}"

Classify as exactly one label:
- disengage: the player is trying to quit, refuse, mock the process, or leave the scene
- continue: anything else, including wrong oath text

Respond with one label only.'''
    return engine.classify(prompt)


def _classify_item_description(engine: GameEngine, message: str) -> str:
    prompt = f'''You are classifying a player reply in a ritual horror game.
The player was asked to describe an object with visual detail so the speaker could picture it.

Player reply: "{message}"

Classify as exactly one label:
- sensory_description: includes concrete visual detail beyond just naming the object
- generic_description: only names the object or stays vague
- unclear: anything else

Respond with one label only.'''
    return engine.classify(prompt)


def _classify_item_meaning(engine: GameEngine, message: str) -> str:
    prompt = f'''You are classifying a player reply in a ritual horror game.
The player was asked why this object was chosen for sacrifice.

Player reply: "{message}"

Classify as exactly one label:
- meaningful: gives a personal reason with emotional or symbolic meaning
- insufficient: gives a weak, generic, or incomplete reason
- deflection: avoids the question, jokes, shrugs it off, or says it was random

Respond with one label only.'''
    return engine.classify(prompt)


def _classify_loss_cost(engine: GameEngine, message: str) -> str:
    prompt = f'''You are classifying a player reply in a ritual horror game.
The player was asked what it costs them to give up the chosen object.

Player reply: "{message}"

Classify as exactly one label:
- clear_loss: clearly describes a real cost, attachment, or emotional loss
- insufficient: does not make the loss clear

Respond with one label only.'''
    return engine.classify(prompt)


def _classify_shame_offer(engine: GameEngine, message: str) -> str:
    prompt = f'''You are classifying a player reply in a ritual horror game.
The player was told to confess a shameful truth.

Player reply: "{message}"

Classify as exactly one label:
- acceptable_shame: a direct, personal, meaningful shame or confession
- refusal: claims to have no shame, refuses, or withholds entirely
- soft_version: gives a filtered, sanitized, safer version instead of the real thing
- insufficient: too vague, too thin, or not personal enough

Respond with one label only.'''
    return engine.classify(prompt)


def _classify_lost_disclosure(engine: GameEngine, message: str) -> str:
    prompt = f'''You are classifying a player reply in a ritual horror game.
The player was asked what they have lost that they cannot get back.

Player reply: "{message}"

Classify as exactly one label:
- personal_loss: a personal memory, moment, relationship, opportunity, or other intangible loss
- object: names a physical possession or thing
- insufficient: not personal enough, too vague, or too shallow

Respond with one label only.'''
    return engine.classify(prompt)


def _classify_loss_permanence(engine: GameEngine, message: str) -> str:
    prompt = f'''You are classifying a player reply in a ritual horror game.
The player was asked why the loss is permanent and cannot be recovered.

Player reply: "{message}"

Classify as exactly one label:
- clear_reason: clearly explains why the loss cannot be undone or recovered
- deflection: avoids the question, refuses it, or answers around it
- insufficient: still too vague or emotionally unclear

Respond with one label only.'''
    return engine.classify(prompt)


def main() -> None:
    config = GameConfig(
        player_name="Sophie",
        state_file=".threshold_progress.json",
        test_mode=True,
    )
    engine = GameEngine(config)
    engine.run_scene(run_scene)


if __name__ == "__main__":
    main()
