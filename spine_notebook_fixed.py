#!/usr/bin/env python3
"""Notebook-safe helper module for Project 6 SPINE workflows.

This file is a clean, standalone entrypoint intended for copy/paste use in
All of Us Researcher Workbench notebooks.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


def default_output_dir() -> str:
    """Return script-safe or notebook-safe output directory."""
    if "__file__" in globals():
        return str(Path(__file__).resolve().parent / "project6_outputs")
    return str((Path.cwd() / "project6_outputs").resolve())


def print_tables_fully(
    tables: dict[str, pd.DataFrame],
    *,
    max_rows: int | None = None,
    max_cols: int | None = None,
    max_colwidth: int | None = None,
) -> None:
    """Print all DataFrames completely (or with explicit limits)."""
    row_opt = max_rows if max_rows is not None else None
    col_opt = max_cols if max_cols is not None else None
    with pd.option_context(
        "display.max_rows",
        row_opt,
        "display.max_columns",
        col_opt,
        "display.max_colwidth",
        max_colwidth,
        "display.width",
        0,
    ):
        for name, df in tables.items():
            print(f"\n===== {name} | rows={len(df):,} cols={df.shape[1]} =====")
            print(df.to_string(index=False))


def strip_git_conflict_markers(text: str) -> str:
    """Remove accidental git conflict markers from pasted notebook code."""
    bad_prefixes = ("<<<<<<<", "=======", ">>>>>>>")
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(bad_prefixes)
    )


@dataclass(frozen=True)
class GeneratedDomainSpec:
    name: str
    table: str
    concept_col: str
    concept_ids: tuple[int, ...]
    datetime_col: str


GENERATED_DOMAIN_SPECS: tuple[GeneratedDomainSpec, ...] = (
    GeneratedDomainSpec(
        name="drug",
        table="drug_exposure",
        concept_col="drug_concept_id",
        concept_ids=(1123618, 1503297),
        datetime_col="drug_exposure_start_datetime",
    ),
    GeneratedDomainSpec(
        name="measurement",
        table="measurement",
        concept_col="measurement_concept_id",
        concept_ids=(1002597, 3004249, 3004410, 3012888, 3025315, 3031203, 3037110, 4245997),
        datetime_col="measurement_datetime",
    ),
    GeneratedDomainSpec(
        name="condition",
        table="condition_occurrence",
        concept_col="condition_concept_id",
        concept_ids=(137548, 198520, 36717608, 4134121, 4134122, 4167097, 4187244, 608177, 761918, 77079, 79119, 80816),
        datetime_col="condition_start_datetime",
    ),
)


def _require_workspace_cdr() -> str:
    cdr = os.environ.get("WORKSPACE_CDR", "").strip()
    if not cdr:
        raise EnvironmentError("WORKSPACE_CDR is not set in this notebook runtime.")
    return cdr


def cohort_filter_sql(dataset: str, person_alias: str) -> str:
    """Cohort filter reused by generated extract SQL blocks."""
    return f"""
{person_alias}.person_id IN (SELECT DISTINCT person_id FROM `{dataset}.cb_search_person`)
""".strip()


def run_query(sql: str) -> pd.DataFrame:
    return pd.read_gbq(
        sql,
        dialect="standard",
        use_bqstorage_api=("BIGQUERY_STORAGE_API_ENABLED" in os.environ),
        progress_bar_type="tqdm_notebook",
    )


def generated_person_sql(dataset: str) -> str:
    where_clause = cohort_filter_sql(dataset, "person")
    return f"""
SELECT person_id, gender_concept_id, race_concept_id, ethnicity_concept_id, sex_at_birth_concept_id
FROM `{dataset}.person` person
WHERE {where_clause}
""".strip()


def generated_domain_sql(spec: GeneratedDomainSpec, dataset: str) -> str:
    where_clause = cohort_filter_sql(dataset, "d")
    concept_list = ", ".join(str(v) for v in spec.concept_ids)
    return f"""
SELECT *
FROM `{dataset}.{spec.table}` d
WHERE d.{spec.concept_col} IN ({concept_list})
  AND {where_clause}
  AND d.{spec.datetime_col} IS NOT NULL
""".strip()


def generated_survey_sql(dataset: str) -> str:
    where_clause = cohort_filter_sql(dataset, "answer")
    return f"""
SELECT person_id, survey_datetime, survey, question_concept_id, answer_concept_id, answer
FROM `{dataset}.ds_survey` answer
WHERE question_concept_id IN (1586134, 1585855)
  AND {where_clause}
""".strip()


def extract_generated_exports(dataset: str | None = None) -> dict[str, pd.DataFrame]:
    dataset = dataset or _require_workspace_cdr()
    extracts: dict[str, pd.DataFrame] = {"person": run_query(generated_person_sql(dataset))}
    for spec in GENERATED_DOMAIN_SPECS:
        extracts[spec.name] = run_query(generated_domain_sql(spec, dataset))
    extracts["survey"] = run_query(generated_survey_sql(dataset))
    return extracts


if __name__ == "__main__":
    print("spine_notebook_fixed.py loaded. Use extract_generated_exports() in notebooks.")
