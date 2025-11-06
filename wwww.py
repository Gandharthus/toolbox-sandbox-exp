from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class TriggerHourlySchedule(BaseModel):
    minute: Union[int, List[int]] = Field(
        default=0,
        description="The minute(s) past each hour when the watch should fire (hourly schedule)."
    )


class TriggerDailyScheduleAtTime(BaseModel):
    hour: Union[int, List[int]] = Field(
        description="Hour(s) of day (0-23) when schedule fires for daily schedule."
    )
    minute: Union[int, List[int]] = Field(
        description="Minute(s) of each specified hour for daily schedule."
    )


class TriggerDailySchedule(BaseModel):
    at: Optional[Union[str, TriggerDailyScheduleAtTime, List[Union[str, TriggerDailyScheduleAtTime]]]] = Field(
        default="midnight",
        description=(
            "Time(s) when the watch should fire each day (daily schedule). "
            "Can be a string like '17:00', a structure {hour, minute}, or list of such."
        )
    )


class TriggerMonthlyScheduleAtTime(BaseModel):
    hour: Union[int, List[int]] = Field(
        description="Hour(s) of day when schedule runs for monthly schedule."
    )
    minute: Union[int, List[int]] = Field(
        description="Minute(s) of hour when schedule runs for monthly schedule."
    )


class TriggerMonthlySchedule(BaseModel):
    on: Union[int, List[int]] = Field(
        description="Day(s) of the month (1-31) when the watch should fire for monthly schedule."
    )
    at: Optional[Union[str, TriggerMonthlyScheduleAtTime, List[Union[str, TriggerMonthlyScheduleAtTime]]]] = Field(
        default="midnight",
        description=(
            "Time(s) on the specified day(s) when the watch should fire (monthly schedule). "
            "Same format as daily schedule 'at'."
        )
    )


class TriggerSchedule(BaseModel):
    interval: Optional[str] = Field(
        default=None,
        description="Fixed interval for schedule (e.g., '5m', '1h', '2d')."
    )
    cron: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Cron expression(s) for schedule execution."
    )
    hourly: Optional[TriggerHourlySchedule] = Field(
        default=None,
        description="Hourly schedule settings."
    )
    daily: Optional[TriggerDailySchedule] = Field(
        default=None,
        description="Daily schedule settings."
    )
    monthly: Optional[Union[TriggerMonthlySchedule, List[TriggerMonthlySchedule]]] = Field(
        default=None,
        description="Monthly schedule settings (single or list)."
    )
    timezone: Optional[str] = Field(
        default=None,
        description="Time‐zone identifier (e.g., 'UTC', 'Europe/Paris') for schedule."
    )

    @field_validator('*', mode='before')
    def check_one_schedule_type(cls, v, values, field):
        # ensure only one of interval/cron/hourly/daily/monthly is used
        if v is not None:
            other_keys = {k for k in values if values.get(k) is not None and k != field.name}
            if other_keys:
                raise ValueError(f"Multiple schedule types provided: {field.name} plus {other_keys}")
        return v


class Trigger(BaseModel):
    schedule: TriggerSchedule = Field(
        description="Trigger definition controlling when the watch executes."
    )


class SearchInputRequest(BaseModel):
    indices: Optional[List[str]] = Field(
        default=None,
        description="List of index names to search."
    )
    indices_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Advanced index options (e.g., allow_no_indices, ignore_unavailable)."
    )
    search_type: Optional[str] = Field(
        default=None,
        description="The search type (e.g., 'query_then_fetch')."
    )
    body: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The Elasticsearch search DSL body."
    )
    timeout: Optional[str] = Field(
        default=None,
        description="Timeout for the search request (e.g., '30s')."
    )


class SearchInput(BaseModel):
    request: SearchInputRequest = Field(
        description="Definition of the actual search request."
    )


class HttpInputRequest(BaseModel):
    scheme: Optional[str] = Field(
        default="https",
        description="HTTP scheme to use for request (http or https)."
    )
    host: Optional[str] = Field(
        default=None,
        description="Host for HTTP request."
    )
    port: Optional[int] = Field(
        default=None,
        description="Port for HTTP request."
    )
    path: Optional[str] = Field(
        default=None,
        description="URL path of the HTTP request."
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Query parameters for HTTP request."
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="HTTP headers to send."
    )
    body: Optional[Union[str, Dict[str, Any]]] = Field(
        default=None,
        description="Body payload for HTTP request."
    )


class HttpInput(BaseModel):
    request: HttpInputRequest = Field(
        description="HTTP input request definition."
    )


class Input(BaseModel):
    search: Optional[SearchInput] = Field(
        default=None,
        description="Search‐type input that queries Elasticsearch indices."
    )
    http: Optional[HttpInput] = Field(
        default=None,
        description="HTTP input that invokes an external endpoint."
    )
    # You may add chain/script/none etc if needed.

    @field_validator('*', mode='before')
    def check_one_input_type(cls, v, values, field):
        if v is not None:
            other_keys = {k for k in values if values.get(k) is not None and k != field.name}
            if other_keys:
                raise ValueError(f"Multiple input types specified: {field.name} plus {other_keys}")
        return v


class CompareCondition(BaseModel):
    __root__: Dict[str, Dict[str, Any]] = Field(
        description=(
            "Structure mapping context‐variable path to comparison details, e.g. "
            `{"ctx.payload.hits.total": {"gt": 5}}`
        )
    )


class ScriptCondition(BaseModel):
    lang: Optional[str] = Field(
        default="painless",
        description="Script language, defaults to painless."
    )
    source: str = Field(
        description="Script source code to execute for condition."
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters to the script."
    )


class ArrayCompareCondition(BaseModel):
    path: str = Field(
        description="Path in payload to array to evaluate."
    )
    gte: Optional[int] = Field(default=None, description="Greater or equal threshold.")
    gt: Optional[int] = Field(default=None, description="Greater than threshold.")
    lte: Optional[int] = Field(default=None, description="Less or equal threshold.")
    lt: Optional[int] = Field(default=None, description="Less than threshold.")


class Condition(BaseModel):
    always: Optional[Dict[str, Any]] = Field(
        default=None,
        description="An always‐true condition (no check)."
    )
    never: Optional[Dict[str, Any]] = Field(
        default=None,
        description="An always‐false condition (never fire)."
    )
    compare: Optional[CompareCondition] = Field(
        default=None,
        description="Compare condition type."
    )
    script: Optional[ScriptCondition] = Field(
        default=None,
        description="Script condition type."
    )
    array_compare: Optional[ArrayCompareCondition] = Field(
        default=None,
        description="Array compare condition for arrays in payload."
    )

    @field_validator('*', mode='before')
    def check_one_condition_type(cls, v, values, field):
        if v is not None:
            other_keys = {k for k, val in values.items() if val is not None and k != field.name}
            if other_keys:
                raise ValueError(f"Multiple condition types specified: {field.name} plus {other_keys}")
        return v


class ScriptTransform(BaseModel):
    lang: Optional[str] = Field(
        default="painless",
        description="Script language for transform."
    )
    source: str = Field(
        description="Script source code for transform."
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters to the script."
    )


class IndexTransform(BaseModel):
    index: str = Field(
        description="Target index where transformed documents will be written."
    )
    doc_id: Optional[str] = Field(
        default=None,
        description="Document ID to use when indexing (optional)."
    )
    refresh: Optional[str] = Field(
        default=None,
        description="Refresh policy (true, false, wait_for)."
    )
    op_type: Optional[str] = Field(
        default=None,
        description="Operation type (index or create)."
    )


class TransformChainElement(BaseModel):
    script: Optional[ScriptTransform] = Field(
        default=None,
        description="Script transform step."
    )
    search: Optional[SearchInput] = Field(
        default=None,
        description="Search transform step."
    )
    index: Optional[IndexTransform] = Field(
        default=None,
        description="Index transform step."

    )

    @field_validator('*', mode='before')
    def only_one_transform_type(cls, v, values, field):
        if v is not None:
            other_keys = {k for k, val in values.items() if val is not None and k != field.name}
            if other_keys:
                raise ValueError(f"Only one transform type allowed per chain element: {field.name} plus {other_keys}")
        return v


class Transform(BaseModel):
    chain: Optional[List[TransformChainElement]] = Field(
        default=None,
        description="List of transform steps executed in order."
    )
    script: Optional[ScriptTransform] = Field(
        default=None,
        description="Single script transform."
    )
    search: Optional[SearchInput] = Field(
        default=None,
        description="Single search transform." 
    )

    @field_validator('*', mode='before')
    def only_one_transform_top_type(cls, v, values, field):
        if v is not None:
            other_keys = {k for k, val in values.items() if val is not None and k != field.name}
            if other_keys:
                raise ValueError(f"Only one transform type allowed: {field.name} plus {other_keys}")
        return v


class ActionBase(BaseModel):
    throttle_period: Optional[str] = Field(
        default=None,
        description="Minimum period between action executions (e.g., '10m')."
    )
    throttle_period_in_millis: Optional[int] = Field(
        default=None,
        description="Minimum period in milliseconds between action executions."
    )
    condition: Optional[Condition] = Field(
        default=None,
        description="Condition to apply before running this action."
    )
    foreach: Optional[str] = Field(
        default=None,
        description="Context variable path to iterate over for multi‐action execution."
    )
    max_iterations: Optional[int] = Field(
        default=None,
        description="Maximum number of iterations for foreach processing."
    )


class LoggingAction(ActionBase):
    logging: Dict[str, Any] = Field(
        description="Logging action configuration (e.g., text, level, category).")


class IndexAction(ActionBase):
    index: Dict[str, Any] = Field(
        description="Index action configuration (index target, doc_id, op_type, refresh).")


class WebhookAction(ActionBase):
    webhook: Dict[str, Any] = Field(
        description="Webhook action configuration (method, host, path, headers, body).")


class EmailAction(ActionBase):
    email: Dict[str, Any] = Field(
        description="Email action configuration (to, subject, body, attachments).")


class PagerDutyAction(ActionBase):
    pagerduty: Dict[str, Any] = Field(
        description="PagerDuty action configuration (account, service_key, incident_key).")


class SlackAction(ActionBase):
    slack: Dict[str, Any] = Field(
        description="Slack action configuration (account, message, attachments).")


Action = Union[
    LoggingAction,
    IndexAction,
    WebhookAction,
    EmailAction,
    PagerDutyAction,
    SlackAction,
]


class Actions(BaseModel):
    __root__: Dict[str, Action] = Field(
        description="Map of action names to their configurations.")


class WatcherWatch(BaseModel):
    trigger: Trigger = Field(
        description="Trigger schedule for the watch.")
    input: Optional[Input] = Field(
        default=None,
        description="Input definition that loads data into watch context.")
    condition: Optional[Condition] = Field(
        default=None,
        description="Condition evaluated on input payload to decide if actions run.")
    transform: Optional[Transform] = Field(
        default=None,
        description="Optional transform applied to payload before actions.")
    actions: Actions = Field(
        description="Definition of actions to take when condition is met.")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Arbitrary metadata for the watch (can include name, description, tags).")
    version: Optional[int] = Field(
        default=None,
        description="Version number for concurrency control when updating watch.")
    active: Optional[bool] = Field(
        default=None,
        description="Whether the watch is enabled (true) or disabled (false).")
    throttle_period: Optional[str] = Field(
        default=None,
        description="Default throttle period for all actions in this watch (e.g., '1h').")
    throttle_period_in_millis: Optional[int] = Field(
        default=None,
        description="Default throttle period in milliseconds for all actions in this watch.")

    class Config:
        extra = "allow"
        schema_extra = {
            "example": {
                "trigger": {
                    "schedule": {
                        "daily": {
                            "at": "17:00"
                        },
                        "timezone": "Europe/Paris"
                    }
                },
                "input": {
                    "search": {
                        "request": {
                            "indices": ["logs-*"],
                            "body": {
                                "query": {"match": {"level": "ERROR"}}
                            }
                        }
                    }
                },
                "condition": {
                    "compare": {"ctx.payload.hits.total": {"gt": 0}}
                },
                "actions": {
                    "alert_team": {
                        "logging": {"text": "Found errors: {{ctx.payload.hits.total}}", "level": "warn"}
                    }
                },
                "metadata": {"watch_name": "error_watch", "team": "observability"},
                "version": 1,
                "active": True
            }
        }