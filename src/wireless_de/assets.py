from pathlib import Path

from dagster import Config, Definitions, RetryPolicy, asset

from wireless_de.contract import validate_snapshot
from wireless_de.settings import Settings
from wireless_de.source import ingest
from wireless_de.warehouse import load_candidate, publish, run_dbt


class RunConfig(Config):
    project: str
    root: str
    work: str
    start: str
    end: str
    page_size: int = 5000
    max_pages: int = 100
    refresh: bool = False
    offline: bool = False


@asset(retry_policy=RetryPolicy(max_retries=1, delay=1))
def fcc_snapshot(context, config: RunConfig):
    values = config.model_dump()
    work = values.pop("work")
    result = ingest(Settings(**values).validate())
    context.add_output_metadata({"rows": result["manifest"]["expected_rows"], "cache_hit": result["cache_hit"]})
    return {**result, "work": work}


@asset
def contracted_rows(context, fcc_snapshot):
    result = validate_snapshot(fcc_snapshot, Path(fcc_snapshot["work"]))
    context.add_output_metadata({"accepted": result["rows"], "rejected": 0})
    return result


@asset
def warehouse_candidate(contracted_rows):
    return load_candidate(contracted_rows)


@asset
def dbt_quality_gate(context, warehouse_candidate):
    result = run_dbt(warehouse_candidate)
    context.add_output_metadata({"tests_passed": result["dbt_results"]["tests_passed"]})
    return result


@asset
def published_data_product(context, dbt_quality_gate):
    result = publish(dbt_quality_gate)
    context.add_output_metadata({"release": result["release"], "rows": result["summary"]["warehouse_rows"]})
    return result


ALL_ASSETS = [fcc_snapshot, contracted_rows, warehouse_candidate, dbt_quality_gate, published_data_product]
defs = Definitions(assets=ALL_ASSETS)
