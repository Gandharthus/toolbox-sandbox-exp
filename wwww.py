from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class TriggerSchedule(BaseModel):
    interval: Optional[str] = None  # e.g. "5m", "1h"
    cron: Optional[str] = None      # e.g. cron expression
    # You can add other schedule types if required (yearly, monthly…)
    

class Trigger(BaseModel):
    schedule: TriggerSchedule


class SearchInputRequest(BaseModel):
    indices: Optional[List[str]] = None
    indices_options: Optional[Dict[str, Any]] = None
    search_type: Optional[str] = None
    body: Optional[Dict[str, Any]] = None
    extract: Optional[List[str]] = None
    timeout: Optional[str] = None


class SearchInput(BaseModel):
    request: SearchInputRequest


class HttpInputRequest(BaseModel):
    host: Optional[str] = None
    scheme: Optional[str] = None
    port: Optional[int] = None
    path: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[Union[str, Dict[str, Any]]] = None


class HttpInput(BaseModel):
    request: HttpInputRequest


class Input(BaseModel):
    # Only listing two major types; you may add “simple”, “chain”, etc as needed
    search: Optional[SearchInput] = None
    http: Optional[HttpInput] = None
    # Could add "chain", "script", "none" etc depending on your usage.
    
    @validator("*", pre=True, always=True)
    def only_one_input_type(cls, v, values, field):
        # ensure only one input type populated
        others = [k for k in values if values[k] not in (None, {})]
        if len(others) > 1:
            raise ValueError("Only one input type may be specified")
        return v


class CompareCondition(BaseModel):
    # e.g. { "ctx.payload.hits.total": { "gt": 5 } }
    __root__: Dict[str, Dict[str, Any]]


class ScriptCondition(BaseModel):
    lang: Optional[str] = Field(default="painless")
    source: str
    params: Optional[Dict[str, Any]] = None


class ArrayCompareCondition(BaseModel):
    path: str
    gte: Optional[int] = None
    gt: Optional[int] = None
    lte: Optional[int] = None
    lt: Optional[int] = None


class Condition(BaseModel):
    always: Optional[Dict[str, Any]] = None
    never: Optional[Dict[str, Any]] = None
    compare: Optional[CompareCondition] = None
    script: Optional[ScriptCondition] = None
    array_compare: Optional[ArrayCompareCondition] = None
    
    @validator('*', pre=True, always=True)
    def only_one_condition_type(cls, v, values, field):
        if v is not None:
            other_fields = [k for k, val in values.items() if val is not None and k != field.name]
            if other_fields:
                raise ValueError("Only one condition type may be specified")
        return v


class TransformChainElement(BaseModel):
    # For a chain transform
    script: Optional[ScriptCondition] = None
    search: Optional[SearchInput] = None
    # could add index or other types if needed


class Transform(BaseModel):
    chain: Optional[List[TransformChainElement]] = None
    script: Optional[ScriptCondition] = None
    search: Optional[SearchInput] = None
    # Optional index transform if required


class ActionBase(BaseModel):
    throttle_period: Optional[str] = None
    throttle_period_in_millis: Optional[int] = None
    condition: Optional[Condition] = None
    foreach: Optional[str] = None
    max_iterations: Optional[int] = None
    

class LoggingAction(ActionBase):
    logging: Dict[str, Any]  # e.g. {"text": "...", "level": "info", "category": "..."}
    
    
class IndexAction(ActionBase):
    index: Dict[str, Any]  # e.g. {"index": "my-index", "doc_id": "...", "refresh": "wait_for", "op_type": "index"}
    
    
class WebhookAction(ActionBase):
    webhook: Dict[str, Any]  # e.g. {"method":"POST","host":"...", "path":"...", "body":"...","headers":{...}}
    
    
class EmailAction(ActionBase):
    email: Dict[str, Any]  # e.g. {"to":"...","subject":"...","body":"...","attachments":{...}}
    
    
class PagerDutyAction(ActionBase):
    pagerduty: Dict[str, Any]  # e.g. {"account": "...", "service_key":"...", "incident_key":"..."}
    
    
class SlackAction(ActionBase):
    slack: Dict[str, Any]  # e.g. {"account":"...", "message":"..."}
    
    
Action = Union[
    LoggingAction,
    IndexAction,
    WebhookAction,
    EmailAction,
    PagerDutyAction,
    SlackAction,
]


class Actions(BaseModel):
    __root__: Dict[str, Action]


class Watch(BaseModel):
    # This is the top-level watch definition to submit via PUT or POST
    trigger: Trigger
    input: Optional[Input] = None
    condition: Optional[Condition] = None
    transform: Optional[Transform] = None
    actions: Actions
    metadata: Optional[Dict[str, Any]] = None
    version: Optional[int] = None  # explicit version control
    active: Optional[bool] = None
    throttle_period: Optional[str] = None
    throttle_period_in_millis: Optional[int] = None

    class Config:
        extra = "allow"
        schema_extra = {
            "example": {
                "trigger": { "schedule": { "interval": "5m" } },
                "input": {
                    "search": {
                        "request": {
                            "indices": ["logs-*"],
                            "body": {
                                "query": { "match": { "level": "ERROR" } }
                            }
                        }
                    }
                },
                "condition": {
                    "compare": { "ctx.payload.hits.total": { "gt": 0 } }
                },
                "actions": {
                    "log_error": {
                        "logging": { "text": "Found errors: {{ctx.payload.hits.total}}", "level": "warn" }
                    }
                },
                "metadata": { "watch_name": "error-watch", "team": "observability" },
                "version": 1,
                "active": True
            }
        }