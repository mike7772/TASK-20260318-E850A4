from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldRule:
    key: str
    label: str
    required: bool
    field_type: str  # "string" | "number" | "date" | "email"
    min_len: int | None = None
    max_len: int | None = None
    min_value: float | None = None
    max_value: float | None = None


APPLICATION_FORM: list[FieldRule] = [
    FieldRule("title", "Title", True, "string", min_len=3, max_len=255),
    FieldRule("deadline", "Deadline (ISO)", True, "date"),
    FieldRule("description", "Description", False, "string", max_len=2000),
    FieldRule("requested_amount", "Requested amount", False, "number", min_value=0, max_value=1_000_000),
    FieldRule("category", "Category", False, "string", max_len=128),
]


def get_application_form_definition():
    return {
        "fields": [r.__dict__ for r in APPLICATION_FORM],
    }


def validate_application_payload(payload: dict) -> list[dict]:
    errors: list[dict] = []
    for rule in APPLICATION_FORM:
        value = payload.get(rule.key)
        if rule.required and (value is None or (isinstance(value, str) and not value.strip())):
            errors.append({"field": rule.key, "code": "REQUIRED"})
            continue
        if value is None:
            continue
        if rule.field_type == "string":
            if not isinstance(value, str):
                errors.append({"field": rule.key, "code": "TYPE"})
                continue
            if rule.min_len is not None and len(value) < rule.min_len:
                errors.append({"field": rule.key, "code": "MIN_LEN"})
            if rule.max_len is not None and len(value) > rule.max_len:
                errors.append({"field": rule.key, "code": "MAX_LEN"})
        if rule.field_type == "number":
            if not isinstance(value, (int, float)):
                errors.append({"field": rule.key, "code": "TYPE"})
                continue
            if rule.min_value is not None and float(value) < rule.min_value:
                errors.append({"field": rule.key, "code": "MIN"})
            if rule.max_value is not None and float(value) > rule.max_value:
                errors.append({"field": rule.key, "code": "MAX"})
        if rule.field_type == "email":
            if not isinstance(value, str) or "@" not in value:
                errors.append({"field": rule.key, "code": "EMAIL"})
    return errors

