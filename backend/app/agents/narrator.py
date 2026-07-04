from app.schemas.action import ActionIntent, ActionOutcome, ContextPack


def narrate_action_result(
    *,
    intent: ActionIntent,
    context: ContextPack,
    outcome: ActionOutcome,
) -> str:
    location_line = (
        f" Current location: {context.player_location_name}."
        if context.player_location_name
        else ""
    )
    target_line = f" Target: {intent.target_name}." if intent.target_name else ""
    consequences = " ".join(outcome.consequences)
    return f"{outcome.summary}{target_line}{location_line} {consequences}".strip()

