"""The public output contract for the case-study assignment.

`AssignmentAnswer` is exactly the shape the grader compares against `expected` in
sample.jsonl: `{next_message, next_action}`. Nothing else (task_id, rule trails,
scores, engine, latency) belongs here — those live in a separate diagnostics object
built in a later task.
"""
from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class ScheduleTourOptionsCTA(BaseModel):
    """SMS-style CTA: reply with a numbered option."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["schedule_tour"]
    options: list[str]


class ScheduleTourLinkCTA(BaseModel):
    """Email-style CTA: click a link."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["schedule_tour"]
    link: str


CTA = Union[ScheduleTourOptionsCTA, ScheduleTourLinkCTA]


class NextMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: Literal["sms", "email", "voice"]
    send_at: str
    subject: Optional[str] = None
    body: str
    cta: CTA


class StartCadenceAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["start_cadence"]
    name: str


class FollowUpInDaysAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["follow_up_in_days"]
    value: int


class MarkOptedOutAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["mark_opted_out"]
    reason: str


NextAction = Union[StartCadenceAction, FollowUpInDaysAction, MarkOptedOutAction]


class AssignmentAnswer(BaseModel):
    """The exact public export shape. Reject any extra top-level key."""

    model_config = ConfigDict(extra="forbid")

    next_message: NextMessage
    next_action: NextAction = Field(discriminator="type")
