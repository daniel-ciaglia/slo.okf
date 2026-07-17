"""Field-pass models: one Pydantic model per known `type` in VOCABULARY.md.

Unknown `type` values fall back to `ConceptBase` — OKF's conformance rules say
consumers MUST NOT reject a bundle for an unrecognized `type`, so we validate
what we can (the cross-cutting fields) and leave the rest alone.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _require_staleness_fields_unless_generated(model: "ConceptBase", type_name: str) -> None:
    """VOCABULARY.md §2: owner/reviewed/review_interval are required unless generated_by is
    present (a structurally-derived fact doesn't need a human review cadence)."""
    if not model.generated_by:
        missing = [f for f in ("owner", "reviewed", "review_interval") if getattr(model, f) is None]
        if missing:
            raise ValueError(
                f"hand-authored {type_name} (no generated_by) missing required field(s): {', '.join(missing)}"
            )


class ConceptBase(BaseModel):
    """Cross-cutting fields from VOCABULARY.md §2. Producer-defined extra keys are allowed."""

    model_config = ConfigDict(extra="allow")

    type: str
    title: Optional[str] = None
    description: Optional[str] = None
    resource: Optional[str] = None
    tags: Optional[list[str]] = None
    timestamp: Optional[str] = None

    owner: Optional[str] = None
    created: Optional[date] = None
    reviewed: Optional[date] = None
    review_interval: Optional[str] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    supersedes: Optional[str] = None
    generated_by: Optional[str] = None


class CustomerJourney(ConceptBase):
    type: Literal["CustomerJourney"]
    title: str
    description: str
    slos: list[str] = Field(min_length=1)
    subsystems: list[str] = Field(default_factory=list)


class Service(ConceptBase):
    type: Literal["Service"]
    title: str
    slos: list[str] = Field(default_factory=list)


class Subsystem(ConceptBase):
    type: Literal["Subsystem"]
    title: str
    resource: str
    journeys: list[str] = Field(default_factory=list)
    service: Optional[str] = None

    @model_validator(mode="after")
    def _staleness_fields_required_when_hand_authored(self) -> "Subsystem":
        _require_staleness_fields_unless_generated(self, "Subsystem")
        return self


class DataSource(ConceptBase):
    type: Literal["DataSource"]
    title: str
    resource: str


class Metric(ConceptBase):
    type: Literal["Metric"]
    title: str
    resource: str
    data_source: Optional[str] = None


class RatioMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")
    good: str
    total: str


class SLI(ConceptBase):
    type: Literal["SLI"]
    title: str
    description: str
    ratio_metric: Optional[RatioMetric] = None
    threshold_metric: Optional[str] = None
    data_source: Optional[str] = None

    @model_validator(mode="after")
    def _exactly_one_indicator(self) -> "SLI":
        if bool(self.ratio_metric) == bool(self.threshold_metric):
            raise ValueError("SLI must set exactly one of ratio_metric or threshold_metric")
        return self


class SLO(ConceptBase):
    type: Literal["SLO"]
    title: str
    description: str
    sli: str
    target: str
    time_window: str
    journey: Optional[str] = None

    @model_validator(mode="after")
    def _staleness_fields_required_when_hand_authored(self) -> "SLO":
        _require_staleness_fields_unless_generated(self, "SLO")
        return self


class Alert(ConceptBase):
    type: Literal["Alert"]
    title: str
    description: str
    severity: Literal["critical", "warning", "info"]
    resource: str
    slo: str
    runbook: str
    notify: Optional[str] = None
    condition_summary: Optional[str] = None

    @model_validator(mode="after")
    def _staleness_fields_required_when_hand_authored(self) -> "Alert":
        _require_staleness_fields_unless_generated(self, "Alert")
        return self


class Runbook(ConceptBase):
    type: Literal["Runbook"]
    title: str
    description: str
    alerts: list[str] = Field(default_factory=list)
    owner: str
    reviewed: date
    review_interval: str


REGISTRY: dict[str, type[ConceptBase]] = {
    "CustomerJourney": CustomerJourney,
    "Service": Service,
    "Subsystem": Subsystem,
    "DataSource": DataSource,
    "Metric": Metric,
    "SLI": SLI,
    "SLO": SLO,
    "Alert": Alert,
    "Runbook": Runbook,
}


def get_model(type_name: str) -> type[ConceptBase]:
    return REGISTRY.get(type_name, ConceptBase)
