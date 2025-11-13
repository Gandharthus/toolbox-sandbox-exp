from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, model_validator


# ---------- Common ----------

class ProcessorBase(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    description: Optional[str] = None
    if_: Optional[Union[str, Dict[str, Any]]] = Field(None, alias="if")
    ignore_failure: Optional[bool] = None
    on_failure: Optional[List["Processor"]] = None
    tag: Optional[str] = None


# ---------- Processor payloads ----------

class AppendProcessor(ProcessorBase):
    field: str
    value: Optional[Union[Any, List[Any]]] = None
    copy_from: Optional[str] = None
    allow_duplicates: Optional[bool] = True

class AttachmentProcessor(ProcessorBase):
    field: str
    ignore_missing: Optional[bool] = False
    indexed_chars: Optional[int] = 100000
    indexed_chars_field: Optional[str] = None
    properties: Optional[List[str]] = None
    target_field: Optional[str] = None
    remove_binary: Optional[bool] = None
    resource_name: Optional[str] = None

class BytesProcessor(ProcessorBase):
    field: str
    target_field: Optional[str] = None
    ignore_missing: Optional[bool] = False

class CircleProcessor(ProcessorBase):
    error_distance: Optional[float] = None
    field: str
    ignore_missing: Optional[bool] = True
    shape_type: Optional[Literal["geo_shape", "shape"]] = None
    target_field: Optional[str] = None

class CommunityIdProcessor(ProcessorBase):
    source_ip: str
    source_port: str
    destination_ip: str
    destination_port: str
    iana_number: Optional[str] = None
    transport: Optional[str] = None
    target_field: Optional[str] = None
    seed: Optional[int] = 0
    ignore_missing: Optional[bool] = True

class ConvertProcessor(ProcessorBase):
    field: str
    type: Literal["integer", "long", "double", "float", "boolean", "ip", "string", "auto"]
    target_field: Optional[str] = None
    ignore_missing: Optional[bool] = False

class CsvProcessor(ProcessorBase):
    field: str
    target_fields: Union[str, List[str]]
    separator: Optional[str] = ","
    quote: Optional[str] = '"'
    empty_value: Optional[Any] = None
    ignore_missing: Optional[bool] = None
    trim: Optional[bool] = None

class DateProcessor(ProcessorBase):
    field: str
    formats: List[str]
    locale: Optional[str] = "ENGLISH"
    target_field: Optional[str] = None
    timezone: Optional[str] = "UTC"
    output_format: Optional[str] = "yyyy-MM-dd'T'HH:mm:ss.SSSXXX"

class DateIndexNameProcessor(ProcessorBase):
    field: str
    index_name_prefix: Optional[str] = None
    date_rounding: Literal["s", "m", "h", "d", "w", "M", "y"]
    timezone: Optional[str] = "UTC"
    index_name_format: Optional[str] = None
    locale: Optional[str] = "ENGLISH"
    # Some versions also support `index_name_timezone`; keep generic to remain future-proof
    index_name_timezone: Optional[str] = None
    formats: Optional[List[str]] = None

class DissectProcessor(ProcessorBase):
    field: str
    pattern: str
    ignore_missing: Optional[bool] = False
    append_separator: Optional[str] = ""

class DotExpanderProcessor(ProcessorBase):
    field: str
    path: Optional[str] = None

class DropProcessor(ProcessorBase):
    pass

class EnrichProcessor(ProcessorBase):
    policy_name: str
    field: Optional[str] = None
    target_field: str
    max_matches: Optional[int] = None
    ignore_missing: Optional[bool] = None
    shape_relation: Optional[Literal["intersects", "disjoint", "within", "contains"]] = None

class FailProcessor(ProcessorBase):
    message: str

class FingerprintProcessor(ProcessorBase):
    fields: Union[str, List[str]]
    target_field: Optional[str] = None
    salt: Optional[str] = None
    method: Optional[Literal["MD5", "SHA-1", "SHA-256", "SHA-512", "MurmurHash3"]] = None
    ignore_missing: Optional[bool] = False

class ForeachProcessor(ProcessorBase):
    field: str
    processor: "Processor"
    ignore_missing: Optional[bool] = False

class GeoIPProcessor(ProcessorBase):
    database_file: Optional[str] = None  # legacy/ip_location alias cases
    field: str
    target_field: Optional[str] = None
    properties: Optional[List[str]] = None
    first_only: Optional[bool] = True
    ignore_missing: Optional[bool] = False
    download_database_on_pipeline_creation: Optional[bool] = None

class GrokProcessor(ProcessorBase):
    field: str
    patterns: List[str]
    pattern_definitions: Optional[Dict[str, str]] = None
    ignore_missing: Optional[bool] = False
    trace_match: Optional[bool] = False
    ecs_compatibility: Optional[Literal["disabled", "v1"]] = "disabled"

class GsubProcessor(ProcessorBase):
    field: str
    pattern: str
    replacement: str
    target_field: Optional[str] = None
    ignore_missing: Optional[bool] = False

class HtmlStripProcessor(ProcessorBase):
    field: str
    target_field: Optional[str] = None
    ignore_missing: Optional[bool] = None

class JoinProcessor(ProcessorBase):
    field: str
    separator: str
    target_field: Optional[str] = None

class JsonProcessor(ProcessorBase):
    field: str
    target_field: Optional[str] = None
    add_to_root: Optional[bool] = None
    add_to_root_conflict_strategy: Optional[Literal["replace", "merge"]] = None
    allow_single_quotes: Optional[bool] = None

class KVProcessor(ProcessorBase):
    field: str
    field_split: Optional[str] = None
    value_split: str
    target_field: Optional[str] = None
    include_keys: Optional[List[str]] = None
    exclude_keys: Optional[List[str]] = None
    ignore_missing: Optional[bool] = None
    trim_key: Optional[str] = None
    trim_value: Optional[str] = None
    prefix: Optional[str] = None

class LowercaseProcessor(ProcessorBase):
    field: str
    target_field: Optional[str] = None
    ignore_missing: Optional[bool] = False

class PipelineProcessor(ProcessorBase):
    name: str
    if_: Optional[Union[str, Dict[str, Any]]] = Field(None, alias="if")
    ignore_missing_pipeline: Optional[bool] = None

class RegisteredDomainProcessor(ProcessorBase):
    field: str
    target_field: Optional[str] = None
    ignore_missing: Optional[bool] = True

class RemoveProcessor(ProcessorBase):
    field: Union[str, List[str]]
    keep: Optional[Union[str, List[str]]] = None
    ignore_missing: Optional[bool] = False

class RenameProcessor(ProcessorBase):
    field: str
    target_field: str
    ignore_missing: Optional[bool] = False

class RerouteProcessor(ProcessorBase):
    destination: Optional[str] = None
    dataset: Optional[Union[str, List[str]]] = None
    namespace: Optional[Union[str, List[str]]] = None

class ScriptProcessor(ProcessorBase):
    id: Optional[str] = None
    source: Optional[str] = None
    lang: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class SetProcessor(ProcessorBase):
    field: str
    value: Optional[Any] = None
    copy_from: Optional[str] = None
    override: Optional[bool] = True
    media_type: Optional[Literal["application/json", "text/plain", "application/x-www-form-urlencoded"]] = None
    ignore_empty_value: Optional[bool] = False

class SetSecurityUserProcessor(ProcessorBase):
    field: str
    properties: Optional[List[Literal["username", "roles", "metadata", "api_key", "realm", "principal", "email", "full_name"]]] = None

class SortProcessor(ProcessorBase):
    field: str
    order: Optional[Literal["asc", "desc"]] = None
    target_field: Optional[str] = None

class SplitProcessor(ProcessorBase):
    field: str
    separator: str
    target_field: Optional[str] = None

class TrimProcessor(ProcessorBase):
    field: str
    target_field: Optional[str] = None
    ignore_missing: Optional[bool] = False

class UppercaseProcessor(ProcessorBase):
    field: str
    target_field: Optional[str] = None
    ignore_missing: Optional[bool] = False

class UrlDecodeProcessor(ProcessorBase):
    field: str
    target_field: Optional[str] = None
    ignore_missing: Optional[bool] = False

class UriPartsProcessor(ProcessorBase):
    field: str
    ignore_missing: Optional[bool] = False
    keep_original: Optional[bool] = True
    target_field: Optional[str] = None

class UserAgentProcessor(ProcessorBase):
    field: str
    target_field: Optional[str] = None
    ignore_missing: Optional[bool] = False
    regex_file: Optional[str] = None
    properties: Optional[List[str]] = None
    extract_device_type: Optional[bool] = None


# ---------- Processor wrapper (JSON shape: {"<name>": {...}}) ----------

class Processor(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    append: Optional[AppendProcessor] = None
    attachment: Optional[AttachmentProcessor] = None
    bytes: Optional[BytesProcessor] = None
    circle: Optional[CircleProcessor] = None
    community_id: Optional[CommunityIdProcessor] = None
    convert: Optional[ConvertProcessor] = None
    csv: Optional[CsvProcessor] = None
    date: Optional[DateProcessor] = None
    date_index_name: Optional[DateIndexNameProcessor] = None
    dissect: Optional[DissectProcessor] = None
    dot_expander: Optional[DotExpanderProcessor] = None
    drop: Optional[DropProcessor] = None
    enrich: Optional[EnrichProcessor] = None
    fail: Optional[FailProcessor] = None
    fingerprint: Optional[FingerprintProcessor] = None
    foreach: Optional[ForeachProcessor] = None
    geoip: Optional[GeoIPProcessor] = None
    grok: Optional[GrokProcessor] = None
    gsub: Optional[GsubProcessor] = None
    html_strip: Optional[HtmlStripProcessor] = None
    join: Optional[JoinProcessor] = None
    json: Optional[JsonProcessor] = None
    kv: Optional[KVProcessor] = None
    lowercase: Optional[LowercaseProcessor] = None
    pipeline: Optional[PipelineProcessor] = None
    registered_domain: Optional[RegisteredDomainProcessor] = None
    remove: Optional[RemoveProcessor] = None
    rename: Optional[RenameProcessor] = None
    reroute: Optional[RerouteProcessor] = None
    script: Optional[ScriptProcessor] = None
    set: Optional[SetProcessor] = None
    set_security_user: Optional[SetSecurityUserProcessor] = None
    sort: Optional[SortProcessor] = None
    split: Optional[SplitProcessor] = None
    trim: Optional[TrimProcessor] = None
    uppercase: Optional[UppercaseProcessor] = None
    urldecode: Optional[UrlDecodeProcessor] = None
    uri_parts: Optional[UriPartsProcessor] = None
    user_agent: Optional[UserAgentProcessor] = None

    @model_validator(mode="after")
    def _one_of(self) -> "Processor":
        set_count = sum(
            v is not None for v in [
                self.append, self.attachment, self.bytes, self.circle, self.community_id,
                self.convert, self.csv, self.date, self.date_index_name, self.dissect,
                self.dot_expander, self.drop, self.enrich, self.fail, self.fingerprint,
                self.foreach, self.geoip, self.grok, self.gsub, self.html_strip, self.join,
                self.json, self.kv, self.lowercase, self.pipeline, self.registered_domain,
                self.remove, self.rename, self.reroute, self.script, self.set,
                self.set_security_user, self.sort, self.split, self.trim, self.uppercase,
                self.urldecode, self.uri_parts, self.user_agent
            ]
        )
        if set_count != 1:
            raise ValueError("Exactly one processor type must be set in a Processor object.")
        return self


# ---------- Pipeline ----------

class IngestPipeline(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    description: Optional[str] = None
    processors: List[Processor]
    on_failure: Optional[List[Processor]] = None
    version: Optional[int] = None
    field_access_pattern: Optional[Literal["classic", "flexible"]] = None
    _meta: Optional[Dict[str, Any]] = None