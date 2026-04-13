from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransitionRule:
    from_state: str
    to_state: str
    role: str
    requires_reason: bool = False


TRANSITIONS: list[TransitionRule] = [
    TransitionRule("Submitted", "Supplemented", "applicant"),
    TransitionRule("Submitted", "Approved", "reviewer"),
    TransitionRule("Submitted", "Rejected", "reviewer", requires_reason=True),
    TransitionRule("Supplemented", "Approved", "reviewer"),
    TransitionRule("Supplemented", "Rejected", "reviewer", requires_reason=True),
    TransitionRule("Submitted", "Canceled", "applicant"),
    TransitionRule("Submitted", "Promoted from Waitlist", "reviewer"),
]


def validate_transition(*, from_state: str, to_state: str, role: str, reason: str | None):
    matrix = {(r.from_state, r.to_state, r.role): r for r in TRANSITIONS}
    rule = matrix.get((from_state, to_state, role))
    if not rule:
        return {
            "ok": False,
            "error": {"code": "INVALID_TRANSITION", "from_state": from_state, "to_state": to_state, "role": role},
        }
    if rule.requires_reason and not reason:
        return {"ok": False, "error": {"code": "REASON_REQUIRED", "from_state": from_state, "to_state": to_state}}
    return {"ok": True}

