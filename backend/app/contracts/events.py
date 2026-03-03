from __future__ import annotations

from pydantic import BaseModel, Field


class BaseDomainEvent(BaseModel):
    schema_version: str = Field(default="1.0.0")
    event_type: str


class InspectionCompleted(BaseDomainEvent):
    event_type: str = Field(default="InspectionCompleted")
    recipe_version: str = Field(default="v1")
    model_version: str = Field(default="v1")
    dataset_version: str = Field(default="v1")


class FeedbackSubmitted(BaseDomainEvent):
    event_type: str = Field(default="FeedbackSubmitted")
    recipe_version: str = Field(default="v1")
    model_version: str = Field(default="v1")
    dataset_version: str = Field(default="v1")


class ModelRetrained(BaseDomainEvent):
    event_type: str = Field(default="ModelRetrained")
    recipe_version: str = Field(default="v1")
    model_version: str = Field(default="v1")
    dataset_version: str = Field(default="v1")


class TrendWarningRaised(BaseDomainEvent):
    event_type: str = Field(default="TrendWarningRaised")
    recipe_version: str = Field(default="v1")
    model_version: str = Field(default="v1")
    dataset_version: str = Field(default="v1")
