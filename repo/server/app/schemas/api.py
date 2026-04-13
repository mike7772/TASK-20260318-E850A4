from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
from pydantic import ConfigDict


class RegisterIn(BaseModel):
    model_config = ConfigDict(extra="ignore")
    username: str
    password: str
    id_number: str | None = None
    phone_number: str | None = None
    email: str | None = None


class ProvisionUserIn(BaseModel):
    username: str
    password: str
    role: Literal["applicant", "reviewer", "financial_admin", "system_admin"]


class LoginIn(BaseModel):
    username: str
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class CreateApplicationIn(BaseModel):
    title: str
    deadline: datetime


class TransitionIn(BaseModel):
    to_state: str
    reason: str | None = None
    expected_version: int = Field(ge=1)


class MaterialIn(BaseModel):
    application_id: int
    checklist_item_id: int
    filename: str
    content: str
    label: Literal["Pending Submission", "Submitted", "Needs Correction"] = "Submitted"
    correction_reason: str | None = None


class BudgetIn(BaseModel):
    application_id: int
    total_budget: float


class TxnIn(BaseModel):
    application_id: int
    type: Literal["income", "expense"]
    amount: float
    invoice_path: str | None = None
    confirm_overspend: bool = False


class RestoreIn(BaseModel):
    backup_path: str
