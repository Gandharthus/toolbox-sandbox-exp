import pytest

# ------------------------------
# VALID JSON FIXTURES (16)
# ------------------------------

@pytest.fixture
def fx_match_simple():
    return {"query": {"match": {"message": "kibana"}}, "size": 10}

@pytest.fixture
def fx_multi_match():
    return {
        "query": {"multi_match": {"query": "elastic agent", "fields": ["title^2", "body"], "type": "best_fields"}},
        "size": 5,
        "from": 0,
    }

@pytest.fixture
def fx_term_verbose():
    return {"query": {"term": {"status": {"value": "ok", "boost": 2.0}}}, "size": 1}

@pytest.fixture
def fx_terms_list():
    return {"query": {"terms": {"env": ["prod", "staging"]}}}

@pytest.fixture
def fx_range_date():
    return {"query": {"range": {"@timestamp": {"gte": "now-7d/d", "lt": "now/d"}}}, "size": 0}

@pytest.fixture
def fx_exists():
    return {"query": {"exists": {"field": "service.name"}}}

@pytest.fixture
def fx_match_all_with_size_from():
    return {"query": {"match_all": {}}, "size": 200, "from": 100}

@pytest.fixture
def fx_ids():
    return {"query": {"ids": {"values": ["a", "b", "c"]}}}

@pytest.fixture
def fx_bool_must_should():
    return {
        "query": {
            "bool": {
                "must": [{"match": {"title": {"query": "observability", "operator": "and"}}}],
                "should": [{"term": {"env": "prod"}}, {"terms": {"team": ["sre", "platform"]}}],
                "minimum_should_match": 1,
            }
        }
    }

@pytest.fixture
def fx_terms_agg_basic():
    return {
        "query": {"match_all": {}},
        "aggs": {"by_env": {"terms": {"field": "env", "size": 10}}},
    }

@pytest.fixture
def fx_date_hist_calendar():
    return {
        "query": {"match_all": {}},
        "aggs": {"per_day": {"date_histogram": {"field": "@timestamp", "calendar_interval": "1d"}}},
    }

@pytest.fixture
def fx_date_hist_fixed():
    return {
        "query": {"match_all": {}},
        "aggs": {"per_hour": {"date_histogram": {"field": "@timestamp", "fixed_interval": "1h"}}},
    }

@pytest.fixture
def fx_histogram_numeric():
    return {
        "query": {"match": {"metric": "latency"}},
        "aggs": {"lat_bins": {"histogram": {"field": "latency_ms", "interval": 50}}},
    }

@pytest.fixture
def fx_range_agg_three():
    return {
        "query": {"match": {"path": "/api"}},
        "aggs": {
            "bytes_ranges": {
                "range": {
                    "field": "bytes",
                    "ranges": [
                        {"to": 1024, "key": "small"},
                        {"from": 1024, "to": 1048576, "key": "medium"},
                        {"from": 1048576, "key": "large"},
                    ],
                }
            }
        },
        "size": 0,
    }

@pytest.fixture
def fx_filters_named():
    return {
        "query": {"match_all": {}},
        "aggs": {
            "status": {
                "filters": {
                    "filters": {
                        "ok": {"term": {"status": "ok"}},
                        "ko": {"term": {"status": {"value": "ko"}}},
                    }
                },
                "aggs": {"avg_bytes": {"avg": {"field": "bytes"}}},
            }
        },
    }

@pytest.fixture
def fx_nested_depth3():
    # depth = 3: terms -> date_histogram -> stats
    return {
        "query": {"match_all": {}},
        "aggs": {
            "by_host": {
                "terms": {"field": "host.name", "size": 5},
                "aggs": {
                    "per_day": {
                        "date_histogram": {"field": "@timestamp", "calendar_interval": "1d"},
                        "aggs": {"bytes_stats": {"stats": {"field": "bytes"}}},
                    }
                },
            }
        },
    }


# ------------------------------
# INVALID JSON FIXTURES (8)
# ------------------------------

@pytest.fixture
def inv_terms_size_over_cap():
    # size = 1001 (over cap 1000)
    return {"query": {"match_all": {}}, "aggs": {"too_many": {"terms": {"field": "env", "size": 1001}}}}

@pytest.fixture
def inv_filters_over_cap():
    # build >1000 named filters
    big = {f"k{i}": {"term": {"env": "prod"}} for i in range(1001)}
    return {"query": {"match_all": {}}, "aggs": {"f": {"filters": {"filters": big}}}}

@pytest.fixture
def inv_range_agg_over_cap():
    ranges = [{"to": i} for i in range(1001)]
    return {"query": {"match_all": {}}, "aggs": {"r": {"range": {"field": "n", "ranges": ranges}}}}

@pytest.fixture
def inv_date_hist_both_intervals():
    return {
        "query": {"match_all": {}},
        "aggs": {"h": {"date_histogram": {"field": "@timestamp", "calendar_interval": "1d", "fixed_interval": "1h"}}},
    }

@pytest.fixture
def inv_date_hist_none_interval():
    return {"query": {"match_all": {}}, "aggs": {"h": {"date_histogram": {"field": "@timestamp"}}}}

@pytest.fixture
def inv_agg_two_types_same_node():
    # both 'terms' and 'stats' -> violates one-of
    return {
        "query": {"match_all": {}},
        "aggs": {"bad": {"terms": {"field": "env", "size": 5}, "stats": {"field": "bytes"}}},
    }

@pytest.fixture
def inv_nesting_depth4():
    # depth 4: terms -> date_hist -> terms -> stats
    return {
        "query": {"match_all": {}},
        "aggs": {
            "l1": {
                "terms": {"field": "a", "size": 5},
                "aggs": {
                    "l2": {
                        "date_histogram": {"field": "@timestamp", "calendar_interval": "1d"},
                        "aggs": {
                            "l3": {
                                "terms": {"field": "b", "size": 3},
                                "aggs": {"l4": {"stats": {"field": "c"}}},
                            }
                        },
                    }
                },
            }
        },
    }

@pytest.fixture
def inv_terms_extra_field_forbidden():
    # unknown key 'bogus' in terms body
    return {"query": {"match_all": {}}, "aggs": {"x": {"terms": {"field": "env", "bogus": 1}}}}
    
    
    
    
    
import pytest
from dsl_models import SearchRequestWithAggs


VALID_FIXTURE_NAMES = [
    "fx_match_simple",
    "fx_multi_match",
    "fx_term_verbose",
    "fx_terms_list",
    "fx_range_date",
    "fx_exists",
    "fx_match_all_with_size_from",
    "fx_ids",
    "fx_bool_must_should",
    "fx_terms_agg_basic",
    "fx_date_hist_calendar",
    "fx_date_hist_fixed",
    "fx_histogram_numeric",
    "fx_range_agg_three",
    "fx_filters_named",
    "fx_nested_depth3",
]


@pytest.mark.parametrize("fixture_name", VALID_FIXTURE_NAMES)
def test_instantiate_from_valid_json_fixtures(fixture_name, request):
    """
    For each valid JSON fixture, ensure we can instantiate the DSL Pydantic model.
    """
    payload = request.getfixturevalue(fixture_name)
    model = SearchRequestWithAggs.model_validate(payload)

    # Round-trip basics
    dumped = model.model_dump(by_alias=True, exclude_none=True)

    # Always has query
    assert "query" in dumped

    # If input had 'aggs', ensure preserved
    if "aggs" in payload:
        assert "aggs" in dumped
        assert set(payload["aggs"].keys()) == set(dumped["aggs"].keys())

    # If input had "from", ensure alias round-trip
    if "from" in payload:
        assert dumped["from"] == payload["from"]


def test_specific_shapes_spot_checks(request):
    # Spot check a couple of deeper shapes
    d = SearchRequestWithAggs.model_validate(request.getfixturevalue("fx_filters_named"))\
                              .model_dump(by_alias=True, exclude_none=True)
    assert "filters" in d["aggs"]["status"] and "filters" in d["aggs"]["status"]["filters"]
    assert "avg" in d["aggs"]["status"]["aggs"]["avg_bytes"]

    d2 = SearchRequestWithAggs.model_validate(request.getfixturevalue("fx_nested_depth3"))\
                               .model_dump(by_alias=True, exclude_none=True)
    assert "terms" in d2["aggs"]["by_host"]
    assert "date_histogram" in d2["aggs"]["by_host"]["aggs"]["per_day"]
    assert "stats" in d2["aggs"]["by_host"]["aggs"]["per_day"]["aggs"]["bytes_stats"]
    
    
    
    
    
import pytest
from pydantic import ValidationError
from dsl_models import SearchRequestWithAggs

INVALID_FIXTURE_NAMES = [
    "inv_terms_size_over_cap",
    "inv_filters_over_cap",
    "inv_range_agg_over_cap",
    "inv_date_hist_both_intervals",
    "inv_date_hist_none_interval",
    "inv_agg_two_types_same_node",
    "inv_nesting_depth4",
    "inv_terms_extra_field_forbidden",
]


@pytest.mark.parametrize("fixture_name", INVALID_FIXTURE_NAMES)
def test_invalid_jsons_raise_validation_error(fixture_name, request):
    payload = request.getfixturevalue(fixture_name)
    with pytest.raises(ValidationError):
        SearchRequestWithAggs.model_validate(payload)
        
        
