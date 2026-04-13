from app.core.state_machine import TRANSITIONS, validate_transition


class FSMEngine:
    def __init__(self):
        self.matrix = {(r.from_state, r.to_state, r.role): r for r in TRANSITIONS}

    def validate(self, *, from_state: str, to_state: str, role: str, reason: str | None):
        return validate_transition(from_state=from_state, to_state=to_state, role=role, reason=reason)
