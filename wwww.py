from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# -------------------------
# Trigger / Schedule
# -------------------------

class TriggerHourlySchedule(BaseModel):
    minute: Union[int, List[int]] = Field(
        default=0,
        description="Minute(s) past each hour when the watch fires (0–59). If omitted, defaults to 0."
    )


class TriggerDailyAtHM(BaseModel):
    hour: Union[int, List[int]] = Field(
        description="Hour(s) of day (0–23) when the watch fires."
    )
    minute: Union[int, List[int]] = Field(
        description="Minute(s) for each specified hour (0–59)."
    )


class TriggerDailySchedule(BaseModel):
    at: Optional[Union[str, TriggerDailyAtHM, List[Union[str, TriggerDailyAtHM]]]] = Field(
        default="midnight",
        description="Time(s) each day. String like '17:00', a {hour,minute} object, or a list of those."
    )


class TriggerMonthlyAtHM(BaseModel):
    hour: Union[int, List[int]] = Field(
        description="Hour(s) of day (0–23) for monthly schedule."
    )
    minute: Union[int, List[int]] = Field(
        description="Minute(s) for each specified hour (0–59)."
    )


class TriggerMonthlySchedule(BaseModel):
    on: Union[int, List[int]] = Field(
        description="Day(s) of the month (1–31) when the watch fires."
    )
    at: Optional[Union[str, TriggerMonthlyAtHM, List[Union[str, TriggerMonthlyAtHM]]]] = Field(
        default="midnight",
        description="Time(s) on the specified day(s). Same formats as daily 'at'."
    )


class TriggerSchedule(BaseModel):
    interval: Optional[str] = Field(
        default=None,
        description="Fixed interval (e.g., '5m', '1h', '2d')."
    )
    cron: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Cron expression(s) controlling execution."
    )
    hourly: Optional[TriggerHourlySchedule] = Field(
        default=None,
        description="Hourly schedule."
    )
    daily: Optional[TriggerDailySchedule] = Field(
        default=None,
        description="Daily schedule."
    )
    monthly: Optional[Union[TriggerMonthlySchedule, List[TriggerMonthlySchedule]]] = Field(
        default=None,
        description="Monthly schedule (single or list)."
    )
    timezone: Optional[str] = Field(
        default=None,
        description="IANA timezone (e.g., 'UTC', 'Europe/Paris')."
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _only_one_schedule_kind(self) -> "TriggerSchedule":
        kinds = [k for k in ("interval", "cron", "hourly", "daily", "monthly")
                 if getattr(self, k) not in (None, [], "")]
        if len(kinds) != 1:
            raise ValueError(f"Exactly one schedule type must be set (got: {kinds or 'none'}).")
        return self


class Trigger(BaseModel):
    schedule: TriggerSchedule = Field(
        description="Trigger schedule definition (exactly one of interval/cron/hourly/daily/monthly)."
    )

    model_config = ConfigDict(extra="forbid")


# -------------------------
# Inputs
# -------------------------

class SearchInputRequest(BaseModel):
    indices: Optional[List[str]] = Field(
        default=None,
        description="Indices/aliases to search."
    )
    indices_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Advanced index selection options (allow_no_indices, ignore_unavailable, etc.)."
    )
    search_type: Optional[str] = Field(
        default=None,
        description="Search type (rarely needed in ES 8; usually omit)."
    )
    body: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Request body using the Elasticsearch Query DSL."
    )
    timeout: Optional[str] = Field(
        default=None,
        description="Search timeout (e.g., '30s')."
    )

    model_config = ConfigDict(extra="forbid")


class SearchInput(BaseModel):
    request: SearchInputRequest = Field(
        description="Search request to load data into the watch context."
    )

    model_config = ConfigDict(extra="forbid")


class HttpInputRequest(BaseModel):
    scheme: Optional[Literal["http", "https"]] = Field(
        default="https",
        description="HTTP scheme for the request."
    )
    host: Optional[str] = Field(
        default=None,
        description="Target host."
    )
    port: Optional[int] = Field(
        default=None,
        description="Target port."
    )
    path: Optional[str] = Field(
        default=None,
        description="Request path (e.g., '/api/v1/health')."
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Query string parameters."
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="HTTP headers."
    )
    body: Optional[Union[str, Dict[str, Any]]] = Field(
        default=None,
        description="Request body (string or JSON object)."
    )

    model_config = ConfigDict(extra="allow")  # allow future attributes (auth, timeouts, etc.)


class HttpInput(BaseModel):
    request: HttpInputRequest = Field(
        description="HTTP request spec; response is loaded into the watch context."
    )

    model_config = ConfigDict(extra="forbid")


class SimpleInput(BaseModel):
    data: Dict[str, Any] = Field(
        description="Static payload loaded into the watch context."
    )

    model_config = ConfigDict(extra="forbid")


class ChainInputLink(BaseModel):
    simple: Optional[SimpleInput] = None
    search: Optional[SearchInput] = None
    http: Optional[HttpInput] = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _only_one_chain_input(self) -> "ChainInputLink":
        kinds = [k for k in ("simple", "search", "http") if getattr(self, k) is not None]
        if len(kinds) != 1:
            raise ValueError(f"Each chain link must specify exactly one input type (got: {kinds or 'none'}).")
        return self


class ChainInput(BaseModel):
    inputs: List[ChainInputLink] = Field(
        description="Sequence of inputs whose payloads are merged into the execution context."
    )

    model_config = ConfigDict(extra="forbid")


class Input(BaseModel):
    simple: Optional[SimpleInput] = Field(default=None, description="Static data input.")
    search: Optional[SearchInput] = Field(default=None, description="Elasticsearch search input.")
    http: Optional[HttpInput] = Field(default=None, description="HTTP input.")
    chain: Optional[ChainInput] = Field(default=None, description="Chain of inputs executed in order.")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _only_one_top_input(self) -> "Input":
        kinds = [k for k in ("simple", "search", "http", "chain") if getattr(self, k) is not None]
        if len(kinds) > 1:
            raise ValueError(f"Watch input must define exactly one top-level input (got: {kinds}).")
        return self


# -------------------------
# Conditions
# -------------------------

class CompareCondition(BaseModel):
    # Example: {"ctx.payload.hits.total.value": {"gt": 5}}
    __root__: Dict[str, Dict[str, Any]] = Field(
        description="Map of ctx path to operator/value (gt/gte/lt/lte/eq/ne)."
    )


class ScriptCondition(BaseModel):
    lang: Optional[str] = Field(default="painless", description="Script language. Defaults to painless.")
    source: str = Field(description="Script source returning truthy/falsey.")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Script params.")

    model_config = ConfigDict(extra="forbid")


class ArrayCompareCondition(BaseModel):
    path: str = Field(description="Payload path to array to evaluate.")
    # Any of these numeric bounds may be used (ES evaluates semantics server-side)
    gte: Optional[int] = Field(default=None, description="Greater-or-equal threshold.")
    gt: Optional[int] = Field(default=None, description="Greater-than threshold.")
    lte: Optional[int] = Field(default=None, description="Less-or-equal threshold.")
    lt: Optional[int] = Field(default=None, description="Less-than threshold.")
    value: Optional[Any] = Field(default=None, description="Optional value to compare array elements to.")
    path_to_elements: Optional[str] = Field(
        default=None,
        description="Optional path inside each array element to compare (per docs)."
    )

    model_config = ConfigDict(extra="forbid")


class Condition(BaseModel):
    always: Optional[Dict[str, Any]] = Field(default=None, description="Always-true condition.")
    never: Optional[Dict[str, Any]] = Field(default=None, description="Always-false condition.")
    compare: Optional[CompareCondition] = Field(default=None, description="Compare condition.")
    script: Optional[ScriptCondition] = Field(default=None, description="Scripted condition.")
    array_compare: Optional[ArrayCompareCondition] = Field(default=None, description="Array compare condition.")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _only_one_condition(self) -> "Condition":
        kinds = [k for k in ("always", "never", "compare", "script", "array_compare")
                 if getattr(self, k) is not None]
        if len(kinds) > 1:
            raise ValueError(f"Exactly one condition type must be set (got: {kinds}).")
        return self


# -------------------------
# Transforms
# -------------------------

class ScriptTransform(BaseModel):
    lang: Optional[str] = Field(default="painless", description="Script language.")
    source: str = Field(description="Transform script source.")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Script params.")

    model_config = ConfigDict(extra="forbid")


class TransformChainStep(BaseModel):
    # Watcher supports script/search transforms (others are uncommon)
    script: Optional[ScriptTransform] = Field(default=None, description="Script transform step.")
    search: Optional[SearchInput] = Field(default=None, description="Search transform step.")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _only_one_transform_step(self) -> "TransformChainStep":
        kinds = [k for k in ("script", "search") if getattr(self, k) is not None]
        if len(kinds) != 1:
            raise ValueError(f"Each transform step must specify exactly one transform (got: {kinds or 'none'}).")
        return self


class Transform(BaseModel):
    chain: Optional[List[TransformChainStep]] = Field(default=None, description="Ordered transform steps.")
    script: Optional[ScriptTransform] = Field(default=None, description="Single script transform.")
    search: Optional[SearchInput] = Field(default=None, description="Single search transform.")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _only_one_transform_top(self) -> "Transform":
        kinds = [k for k in ("chain", "script", "search") if getattr(self, k) is not None]
        if len(kinds) > 1:
            raise ValueError(f"Exactly one top-level transform must be set (got: {kinds}).")
        return self


# -------------------------
# Actions
# -------------------------

LogLevel = Literal["trace", "debug", "info", "warn", "error"]

class LoggingActionConfig(BaseModel):
    text: str = Field(description="Log message (supports Mustache templates).")
    level: Optional[LogLevel] = Field(default="info", description="Log level (default: info).")
    category: Optional[str] = Field(default=None, description="Optional logger category/name.")

    model_config = ConfigDict(extra="forbid")


class IndexActionConfig(BaseModel):
    index: str = Field(description="Target index for the document.")
    doc_id: Optional[str] = Field(default=None, description="Optional document ID.")
    refresh: Optional[Literal["true", "false", "wait_for"]] = Field(
        default=None, description="Refresh policy."
    )
    op_type: Optional[Literal["index", "create"]] = Field(
        default=None, description="Operation type."
    )
    doc: Optional[Dict[str, Any]] = Field(
        default=None, description="Document to index (if not provided via transform/payload)."
    )

    model_config = ConfigDict(extra="forbid")


class HttpMethod(str):
    """Lightweight literal-esque type that tolerates future methods"""
    def __new__(cls, value: str) -> "HttpMethod":
        v = str.__new__(cls, value.upper())
        if v not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"}:
            raise ValueError("Unsupported HTTP method for webhook action.")
        return v


class WebhookActionConfig(BaseModel):
    scheme: Optional[Literal["http", "https"]] = Field(default="https", description="HTTP scheme.")
    host: str = Field(description="Remote host.")
    port: Optional[int] = Field(default=None, description="Remote port.")
    method: Optional[HttpMethod] = Field(default=None, description="HTTP method (default per body presence).")
    path: Optional[str] = Field(default=None, description="Request path.")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters.")
    headers: Optional[Dict[str, str]] = Field(default=None, description="HTTP headers.")
    body: Optional[Union[str, Dict[str, Any]]] = Field(default=None, description="Request body.")

    model_config = ConfigDict(extra="allow")  # allow auth, timeouts, etc.


class EmailBody(BaseModel):
    text: Optional[str] = Field(default=None, description="Plain-text body.")
    html: Optional[str] = Field(default=None, description="HTML body.")

    @model_validator(mode="after")
    def _one_of_text_or_html(self) -> "EmailBody":
        if not (self.text or self.html):
            raise ValueError("Email body must include 'text' and/or 'html'.")
        return self

    model_config = ConfigDict(extra="forbid")


class EmailActionConfig(BaseModel):
    to: Union[str, List[str]] = Field(description="Recipient(s).")
    cc: Optional[Union[str, List[str]]] = Field(default=None, description="CC recipient(s).")
    bcc: Optional[Union[str, List[str]]] = Field(default=None, description="BCC recipient(s).")
    subject: str = Field(description="Email subject.")
    body: EmailBody = Field(description="Email body (text and/or HTML).")
    priority: Optional[Literal["low", "normal", "high"]] = Field(
        default=None, description="Email priority."
    )
    attachments: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Attachments configuration (e.g., reports)."
    )

    model_config = ConfigDict(extra="allow")  # allow provider-specific fields


class ActionBase(BaseModel):
    throttle_period: Optional[str] = Field(
        default=None, description="Minimum period between executions (e.g., '10m')."
    )
    throttle_period_in_millis: Optional[int] = Field(
        default=None, description="Minimum period in milliseconds between executions."
    )
    condition: Optional[Condition] = Field(
        default=None, description="Optional action-level condition."
    )
    foreach: Optional[str] = Field(
        default=None, description="Context path to iterate over for repeated action execution."
    )
    max_iterations: Optional[int] = Field(
        default=None, description="Max iterations when using 'foreach'."
    )

    model_config = ConfigDict(extra="forbid")


class LoggingAction(ActionBase):
    logging: LoggingActionConfig = Field(description="Logging action configuration.")


class IndexAction(ActionBase):
    index: IndexActionConfig = Field(description="Index action configuration.")


class WebhookAction(ActionBase):
    webhook: WebhookActionConfig = Field(description="Webhook action configuration.")


class EmailAction(ActionBase):
    email: EmailActionConfig = Field(description="Email action configuration.")


Action = Union[LoggingAction, IndexAction, WebhookAction, EmailAction]


class Actions(BaseModel):
    __root__: Dict[str, Action] = Field(
        description="Map of action names to their configurations."
    )

    model_config = ConfigDict(extra="forbid")


# -------------------------
# Top-level Watch
# -------------------------

class WatcherWatch(BaseModel):
    """
    Elasticsearch Watcher watch definition (Elasticsearch 8.x).
    Includes trigger, input, condition, optional transform, and actions.
    """
    trigger: Trigger = Field(description="Trigger schedule controlling when the watch executes.")
    input: Optional[Input] = Field(default=None, description="Input that populates the execution context.")
    condition: Optional[Condition] = Field(
        default=None,
        description="Condition to decide whether actions run. If omitted, defaults to 'always'."
    )
    transform: Optional[Transform] = Field(
        default=None,
        description="Optional transform to modify the payload before actions."
    )
    actions: Actions = Field(description="Actions to execute when the condition is met.")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Arbitrary metadata (name, description, tags, owner, etc.)."
    )
    version: Optional[int] = Field(
        default=None, description="Version for concurrency control when updating a watch."
    )
    active: Optional[bool] = Field(
        default=None, description="Whether the watch is enabled."
    )
    throttle_period: Optional[str] = Field(
        default=None, description="Default throttle period for all actions (overridden per-action if set)."
    )
    throttle_period_in_millis: Optional[int] = Field(
        default=None, description="Default throttle period for all actions, in milliseconds."
    )

    # allow future fields from ES without breaking deserialization
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def _require_actions(self) -> "WatcherWatch":
        if not self.actions or not self.actions.__root__:
            # ES allows a watch with no actions but it’s rarely useful; keep, but warn by validation?
            # We’ll allow but keep the model permissive.
            pass
        return self