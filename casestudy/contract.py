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


class ScheduleTourReplyCTA(BaseModel):
    """Fallback CTA (C3): no safe link and no option days; the recipient replies to arrange a tour.

    Emitted only with a visible unresolved-link / uncertainty diagnostic. Not observed in the
    samples; kept as the smallest shape that still names the intent.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["schedule_tour"]


CTA = Union[ScheduleTourOptionsCTA, ScheduleTourLinkCTA, ScheduleTourReplyCTA]


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


class NoMessageAction(BaseModel):
    """C7 extension for outcomes the two samples never show: the service proposes no automated
    message and instead reports why (suppressed, escalated for a human, a voice call task, or a
    malformed record). Not observed; a project-defined shape, labeled as such in diagnostics.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["suppress", "escalate", "create_call_task"]
    reason: str


NextAction = Union[StartCadenceAction, FollowUpInDaysAction, MarkOptedOutAction, NoMessageAction]


class AssignmentAnswer(BaseModel):
    """The exact public export shape. Reject any extra top-level key.

    `next_message` is null only when no automated message is proposed (opt-out, suppress,
    escalate, call task, malformed record); both observed samples carry a message.
    """

    model_config = ConfigDict(extra="forbid")

    next_message: Optional[NextMessage]
    next_action: NextAction = Field(discriminator="type")
