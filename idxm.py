from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict


# -----------------------------------------------------------------------------
# Aliases
# -----------------------------------------------------------------------------

class AliasDefinition(BaseModel):
    """
    Defines a single index alias.

    LLM guidance:
      - Use aliases to point reads/writes at indices without changing client code.
      - `filter` is a Query DSL object; pass your earlier Query model’s dump or a raw dict.
      - Set `is_write_index=true` for the active write index in a rolling/ILM setup.

    JSON shape (inside `aliases`):
      "my-alias": {
        "is_write_index": true,
        "filter": { ... Query DSL ... },
        "routing": "shard-key",
        "index_routing": "2",
        "search_routing": "1,2",
        "is_hidden": false
      }
    """
    is_write_index: bool | None = Field(
        None, description="If true, this alias is the write index target."
    )
    filter: dict[str, Any] | None = Field(
        None, description="Query DSL filter limiting documents visible via this alias."
    )
    routing: str | None = Field(
        None, description="Default routing applied to both indexing and search (unless overridden)."
    )
    index_routing: str | None = Field(
        None, description="Routing used specifically for indexing via this alias."
    )
    search_routing: str | None = Field(
        None, description="Routing used specifically for searches via this alias."
    )
    is_hidden: bool | None = Field(
        None, description="If true, the alias is hidden. All target indices must agree."
    )

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------
# Settings (minimal, extend as needed)
# -----------------------------------------------------------------------------

class AnalysisSettings(BaseModel):
    """
    Custom analysis components for text fields.

    LLM guidance:
      - Use `analyzer` for full-text fields (tokenizer + filters).
      - Use `normalizer` for `keyword` fields (no tokenizer; single token).
      - Keys are user-defined component names; values are component configs.

    Example:
      analysis = {
        "analyzer": {
          "my_text": {"type": "custom","tokenizer":"standard","filter":["lowercase","asciifolding"]}
        },
        "normalizer": {
          "folding": {"type":"custom","filter":["lowercase","asciifolding"]}
        }
      }
    """
    analyzer: dict[str, dict[str, Any]] | None = Field(
        None, description="Named analyzers built from tokenizer + token filters (+ char filters)."
    )
    normalizer: dict[str, dict[str, Any]] | None = Field(
        None, description="Named normalizers for keyword fields (no tokenizer; single token)."
    )
    tokenizer: dict[str, dict[str, Any]] | None = Field(
        None, description="Custom tokenizers used by analyzers."
    )
    filter: dict[str, dict[str, Any]] | None = Field(
        None, description="Custom token filters used by analyzers."
    )
    char_filter: dict[str, dict[str, Any]] | None = Field(
        None, description="Custom char filters used by analyzers."
    )

    model_config = ConfigDict(extra="forbid")


class IndexSettings(BaseModel):
    """
    Common index settings (safe subset).

    LLM guidance:
      - `number_of_shards` is static (set only at creation).
      - `number_of_replicas` & `refresh_interval` are dynamic (can change later).
      - `analysis` holds analyzer/normalizer definitions for mappings to reference.
      - If you use ILM, you can include the lifecycle settings below.

    Tip: Keep values small/strings exactly as ES expects (e.g., '30s' for intervals).
    """
    number_of_shards: int | None = Field(
        None, description="Primary shard count. Static at index creation."
    )
    number_of_replicas: int | None = Field(
        None, description="Replica count per primary shard."
    )
    refresh_interval: str | None = Field(
        None, description="How often to refresh (e.g., '1s', '-1' to disable background refresh)."
    )
    analysis: AnalysisSettings | None = Field(
        None, description="Custom analyzers, tokenizers, filters, char filters, and normalizers."
    )

    # Optional ILM-related settings (omit if you use data streams)
    index_lifecycle_name: str | None = Field(
        default=None, alias="index.lifecycle.name",
        description="Name of an ILM policy to apply to this index."
    )
    index_lifecycle_rollover_alias: str | None = Field(
        default=None, alias="index.lifecycle.rollover_alias",
        description="Alias used by ILM for rollover (also set alias is_write_index=true)."
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


# -----------------------------------------------------------------------------
# Mappings (field types and structure)
# -----------------------------------------------------------------------------

# -- Concrete field mappings ---------------------------------------------------

class TextMapping(BaseModel):
    """`text` field: analyzed, full-text searchable. Use for human text."""
    type: Literal["text", "match_only_text"] = "text"
    analyzer: str | None = None
    search_analyzer: str | None = None
    fields: dict[str, "FieldMapping"] | None = Field(
        None, description="Multi-fields (e.g., keyword subfield)."
    )
    index: bool | None = None
    norms: bool | None = None
    store: bool | None = None
    model_config = ConfigDict(extra="forbid")


class KeywordMapping(BaseModel):
    """`keyword`/exact string field for filters/sorts/aggregations."""
    type: Literal["keyword", "constant_keyword", "wildcard"] = "keyword"
    normalizer: str | None = None
    ignore_above: int | None = None
    fields: dict[str, "FieldMapping"] | None = None
    index: bool | None = None
    doc_values: bool | None = None
    store: bool | None = None
    model_config = ConfigDict(extra="forbid")


class NumericMapping(BaseModel):
    """Numeric types (e.g., `long`, `integer`, `short`, `byte`, `double`, `float`, `half_float`, `unsigned_long`)."""
    type: Literal[
        "long", "integer", "short", "byte",
        "double", "float", "half_float", "scaled_float", "unsigned_long"
    ]
    coerce: bool | None = None
    index: bool | None = None
    doc_values: bool | None = None
    scaling_factor: int | None = Field(
        None, description="Required only when type='scaled_float'."
    )
    model_config = ConfigDict(extra="forbid")


class DateMapping(BaseModel):
    """`date` or `date_nanos`."""
    type: Literal["date", "date_nanos"] = "date"
    format: str | None = None
    ignore_malformed: bool | None = None
    index: bool | None = None
    doc_values: bool | None = None
    model_config = ConfigDict(extra="forbid")


class BooleanMapping(BaseModel):
    """`boolean`."""
    type: Literal["boolean"] = "boolean"
    index: bool | None = None
    model_config = ConfigDict(extra="forbid")


class IpMapping(BaseModel):
    """`ip` (IPv4/IPv6)."""
    type: Literal["ip"] = "ip"
    index: bool | None = None
    model_config = ConfigDict(extra="forbid")


class GeoPointMapping(BaseModel):
    """`geo_point`."""
    type: Literal["geo_point"] = "geo_point"
    model_config = ConfigDict(extra="forbid")


class GeoShapeMapping(BaseModel):
    """`geo_shape`."""
    type: Literal["geo_shape"] = "geo_shape"
    model_config = ConfigDict(extra="forbid")


class ObjectMapping(BaseModel):
    """
    `object` (un-nested) for JSON sub-objects.

    LLM guidance:
      - Use `object` for hierarchical JSON where cross-field matches are OK.
      - Use `nested` when you need arrays of objects to be queried independently.
    """
    type: Literal["object"] = "object"
    properties: dict[str, "FieldMapping"] | None = None
    dynamic: bool | Literal["strict", "runtime"] | None = None
    enabled: bool | None = None
    model_config = ConfigDict(extra="forbid")


class NestedMapping(BaseModel):
    """`nested` is like object but preserves per-object relationships in arrays."""
    type: Literal["nested"] = "nested"
    properties: dict[str, "FieldMapping"] | None = None
    dynamic: bool | Literal["strict", "runtime"] | None = None
    model_config = ConfigDict(extra="forbid")


class DenseVectorMapping(BaseModel):
    """`dense_vector` (dimensions & optional indexing specifics vary by version/features)."""
    type: Literal["dense_vector"] = "dense_vector"
    dims: int | None = Field(None, description="Vector dimensionality.")
    # Add optional engine-specific params as needed (e.g., similarity, index options)
    model_config = ConfigDict(extra="allow")  # allow vendor/version-specific keys


class SemanticTextMapping(BaseModel):
    """`semantic_text` for vector-aware semantic search (feature-gated)."""
    type: Literal["semantic_text"] = "semantic_text"
    # Leave options open for model/embedding settings that may evolve
    model_config = ConfigDict(extra="allow")


class CustomFieldMapping(BaseModel):
    """
    Escape hatch for any field type/options not modeled above.

    LLM guidance:
      - Set `type` to any valid ES field type (e.g., `completion`, `flattened`, `percolator`, `range`, etc.).
      - Include any additional keys required by that type.
    """
    type: str
    model_config = ConfigDict(extra="allow")


FieldMapping = (
    TextMapping
    | KeywordMapping
    | NumericMapping
    | DateMapping
    | BooleanMapping
    | IpMapping
    | GeoPointMapping
    | GeoShapeMapping
    | ObjectMapping
    | NestedMapping
    | DenseVectorMapping
    | SemanticTextMapping
    | CustomFieldMapping
)


class RuntimeField(BaseModel):
    """
    Runtime field definition (evaluated at query time; not indexed).

    LLM guidance:
      - Use for fields you want to compute on read (scripted via Painless).
      - `type` is usually a primitive (e.g., 'keyword', 'long', 'double', 'date', 'boolean', 'ip', etc.).
    """
    type: str = Field(..., description="Runtime field value type.")
    script: dict[str, Any] | None = Field(
        None, description="Painless script: {'source': 'emit(...)', 'params': {...}}"
    )
    model_config = ConfigDict(extra="forbid")


class DynamicTemplate(BaseModel):
    """
    One dynamic template entry (wrap into a named object at emit time).

    LLM guidance:
      - Create rules to map *new* fields by name or detected type.
      - Common keys: match_mapping_type, match, path_match, path_unmatch, match_pattern.
      - Provide either a `mapping` (indexed field) or `runtime` (runtime field) block.

    Example authoring helper (name + template body):
      DynamicTemplate(
        name="strings_as_keywords",
        body={
          "match_mapping_type": "string",
          "mapping": {"type": "keyword", "ignore_above": 256}
        }
      )
    """
    name: str = Field(..., description="Template name.")
    body: dict[str, Any] = Field(..., description="Template body object.")

    model_config = ConfigDict(extra="forbid")


class Mappings(BaseModel):
    """
    Index mappings (schema).

    LLM guidance:
      - Put concrete fields in `properties`.
      - Control new-field behavior with `dynamic`: true | false | 'strict' | 'runtime'.
      - Add `runtime` for compute-on-read fields.
      - Use `dynamic_templates` for rules that apply to future (not-yet-seen) fields.
    """
    properties: dict[str, FieldMapping] | None = Field(
        None, description="Field-name → FieldMapping."
    )
    dynamic: bool | Literal["strict", "runtime"] | None = Field(
        None, description="How to handle new fields: true/false/'strict'/'runtime'."
    )
    runtime: dict[str, RuntimeField] | None = Field(
        None, description="Runtime (scripted) fields evaluated on read."
    )
    dynamic_templates: list[DynamicTemplate] | None = Field(
        None, description="Ordered rules; first match wins."
    )

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------
# Index body + helpers
# -----------------------------------------------------------------------------

class IndexDefinition(BaseModel):
    """
    Elasticsearch index definition (request body for `PUT /{index}`).

    LLM guidance:
      - Use `settings` for shards/replicas/refresh/analysis/ILM.
      - Use `mappings` to declare field schema; prefer explicit mappings for critical fields.
      - Use `aliases` to add read/write names (e.g., blue/green or ILM rollover).

    Usage:
      body = IndexDefinition(
        settings=IndexSettings(
          number_of_shards=1,
          number_of_replicas=1,
          refresh_interval="1s",
          analysis=AnalysisSettings(
            analyzer={
              "default_text": {"type":"custom","tokenizer":"standard","filter":["lowercase","asciifolding"]}
            },
            normalizer={
              "folding": {"type":"custom","filter":["lowercase","asciifolding"]}
            }
          ),
          **{"index.lifecycle.name": "my_policy", "index.lifecycle.rollover_alias": "logs-write"}
        ),
        mappings=Mappings(
          dynamic="strict",
          properties={
            "title": TextMapping(type="text", analyzer="default_text", fields={"raw": KeywordMapping(type="keyword")}),
            "tags": KeywordMapping(type="keyword", normalizer="folding"),
            "@timestamp": DateMapping(type="date"),
            "author": ObjectMapping(type="object", properties={"name": KeywordMapping(type="keyword")}),
            "comments": NestedMapping(
              properties={
                "user": KeywordMapping(type="keyword"),
                "message": TextMapping(type="text")
              }
            )
          },
          runtime={
            "day_of_week": RuntimeField(type="keyword", script={"source": "emit(doc['@timestamp'].value.dayOfWeekEnum.toString())"})
          },
          dynamic_templates=[
            DynamicTemplate(
              name="strings_as_keywords",
              body={"match_mapping_type": "string", "mapping": {"type": "keyword", "ignore_above": 256}}
            )
          ]
        ),
        aliases={
          "logs": AliasDefinition(),  # read alias
          "logs-write": AliasDefinition(is_write_index=True)  # write alias
        }
      )

      json_body = body.model_dump(by_alias=True, exclude_none=True)
    """
    settings: IndexSettings | None = None
    mappings: Mappings | None = None
    aliases: dict[str, AliasDefinition] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="forbid")
