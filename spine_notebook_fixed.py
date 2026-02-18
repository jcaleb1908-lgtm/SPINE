#!/usr/bin/env python3
"""SPINE one-file notebook version (copy/paste ready).

Use this single file in All of Us Researcher Workbench notebooks.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


def default_output_dir() -> str:
    """Notebook-safe output directory."""
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
    """Print all DataFrames fully (or with explicit caps)."""
    row_opt = max_rows if max_rows is not None else None
    col_opt = max_cols if max_cols is not None else None
    with pd.option_context(
        "display.max_rows", row_opt,
        "display.max_columns", col_opt,
        "display.max_colwidth", max_colwidth,
        "display.width", 0,
    ):
        for name, df in tables.items():
            print(f"\n===== {name} | rows={len(df):,} cols={df.shape[1]} =====")
            print(df.to_string(index=False))


def strip_git_conflict_markers(text: str) -> str:
    """Remove accidental git conflict markers from pasted code."""
    bad_prefixes = ("<<<<<<<", "=======", ">>>>>>>")
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(bad_prefixes)
    )


def require_workspace_cdr() -> str:
    cdr = os.environ.get("WORKSPACE_CDR", "").strip()
    if not cdr:
        raise EnvironmentError("WORKSPACE_CDR is not set in this notebook runtime.")
    return cdr


def run_query(sql: str) -> pd.DataFrame:
    return pd.read_gbq(
        sql,
        dialect="standard",
        use_bqstorage_api=("BIGQUERY_STORAGE_API_ENABLED" in os.environ),
        progress_bar_type="tqdm_notebook",
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
        concept_ids=(
            1002597, 3004249, 3004410, 3012888, 3025315, 3031203, 3037110,
            37027885, 37045117, 40772572, 40779160, 40782589, 40782590,
            40789535, 40795740, 40795800, 4087496, 4093979, 4099154, 4245997,
        ),
        datetime_col="measurement_datetime",
    ),
    GeneratedDomainSpec(
        name="condition",
        table="condition_occurrence",
        concept_col="condition_concept_id",
        concept_ids=(
            137548, 198520, 36717608, 4134121, 4134122, 4167097,
            4187244, 608177, 761918, 77079, 79119, 80816,
        ),
        datetime_col="condition_start_datetime",
    ),
)


def cohort_filter_sql(dataset: str, person_alias: str) -> str:
    """Shared cohort filter from generated AoU exports."""
    return f"""
{person_alias}.person_id IN (SELECT
    DISTINCT person_id
FROM
    `{dataset}.cb_search_person` cb_search_person
WHERE
    cb_search_person.person_id IN (SELECT
        person_id
    FROM
        `{dataset}.cb_search_person` p
    WHERE
        DATE_DIFF(CURRENT_DATE, dob, YEAR) - IF(EXTRACT(MONTH FROM dob)*100 + EXTRACT(DAY FROM dob) > EXTRACT(MONTH FROM CURRENT_DATE)*100 + EXTRACT(DAY FROM CURRENT_DATE), 1, 0) BETWEEN 40 AND 65
        AND NOT EXISTS (SELECT
            1
        FROM
            `{dataset}.death` d
        WHERE
            d.person_id = p.person_id))
    AND cb_search_person.person_id IN (SELECT
        criteria.person_id
    FROM
        (SELECT
            DISTINCT person_id, concept_id
        FROM
            `{dataset}.cb_search_all_events`
        WHERE
            concept_id IN (SELECT
                DISTINCT c.concept_id
            FROM
                `{dataset}.cb_criteria` c
            JOIN
                (SELECT
                    CAST(cr.id AS STRING) AS id
                FROM
                    `{dataset}.cb_criteria` cr
                WHERE
                    concept_id IN (201826)
                    AND full_text LIKE '%_rank1]%') a
                ON (c.path LIKE CONCAT('%.', a.id, '.%')
                OR c.path LIKE CONCAT('%.', a.id)
                OR c.path LIKE CONCAT(a.id, '.%')
                OR c.path = a.id)
            WHERE
                is_standard = 1
                AND is_selectable = 1)
            AND is_standard = 1)) criteria)
    AND cb_search_person.person_id IN (SELECT
        DISTINCT person_id
    FROM
        `{dataset}.cb_search_all_events`
    WHERE
        concept_id IN (903124)
        AND is_standard = 0)
    AND cb_search_person.person_id NOT IN (SELECT
        criteria.person_id
    FROM
        (SELECT
            DISTINCT person_id, concept_id
        FROM
            `{dataset}.cb_search_all_events`
        WHERE
            concept_id IN (SELECT
                DISTINCT c.concept_id
            FROM
                `{dataset}.cb_criteria` c
            JOIN
                (SELECT
                    CAST(cr.id AS STRING) AS id
                FROM
                    `{dataset}.cb_criteria` cr
                WHERE
                    concept_id IN (24612, 313217, 199074)
                    AND full_text LIKE '%_rank1]%') a
                ON (c.path LIKE CONCAT('%.', a.id, '.%')
                OR c.path LIKE CONCAT('%.', a.id)
                OR c.path LIKE CONCAT(a.id, '.%')
                OR c.path = a.id)
            WHERE
                is_standard = 1
                AND is_selectable = 1)
            AND is_standard = 1)) criteria)
    AND cb_search_person.person_id NOT IN (SELECT
        person_id
    FROM
        `{dataset}.person`
    WHERE
        ethnicity_concept_id IN (903096, 0, 903079, 1586148)
    UNION DISTINCT SELECT
        person_id
    FROM
        `{dataset}.person`
    WHERE
        race_concept_id IN (2100000001, 903096, 45882607, 1177221)
    UNION DISTINCT SELECT
        person_id
    FROM
        `{dataset}.person`
    WHERE
        gender_concept_id IN (2000000002, 0)
    UNION DISTINCT SELECT
        person_id
    FROM
        `{dataset}.person`
    WHERE
        sex_at_birth_concept_id IN (2000000009, 0))
)
"""


def generated_person_sql(dataset: str) -> str:
    where_clause = cohort_filter_sql(dataset, "person")
    return f"""
SELECT
    person.person_id,
    person.gender_concept_id,
    p_gender.concept_name AS gender,
    person.birth_datetime AS date_of_birth,
    person.race_concept_id,
    p_race.concept_name AS race,
    person.ethnicity_concept_id,
    p_ethnicity.concept_name AS ethnicity,
    person.sex_at_birth_concept_id,
    p_sex_at_birth.concept_name AS sex_at_birth,
    person.self_reported_category_concept_id,
    p_self_reported.concept_name AS self_reported_category
FROM `{dataset}.person` person
LEFT JOIN `{dataset}.concept` p_gender ON person.gender_concept_id = p_gender.concept_id
LEFT JOIN `{dataset}.concept` p_race ON person.race_concept_id = p_race.concept_id
LEFT JOIN `{dataset}.concept` p_ethnicity ON person.ethnicity_concept_id = p_ethnicity.concept_id
LEFT JOIN `{dataset}.concept` p_sex_at_birth ON person.sex_at_birth_concept_id = p_sex_at_birth.concept_id
LEFT JOIN `{dataset}.concept` p_self_reported ON person.self_reported_category_concept_id = p_self_reported.concept_id
WHERE {where_clause}
"""


def generated_domain_sql(spec: GeneratedDomainSpec, dataset: str) -> str:
    where_clause = cohort_filter_sql(dataset, "d")
    concept_list = ", ".join(str(v) for v in spec.concept_ids)
    return f"""
SELECT *
FROM `{dataset}.{spec.table}` d
WHERE d.{spec.concept_col} IN ({concept_list})
  AND {where_clause}
  AND d.{spec.datetime_col} IS NOT NULL
"""


def generated_survey_sql(dataset: str) -> str:
    where_clause = cohort_filter_sql(dataset, "answer")
    return f"""
SELECT
    answer.person_id,
    answer.survey_datetime,
    answer.survey,
    answer.question_concept_id,
    answer.question,
    answer.answer_concept_id,
    answer.answer,
    answer.survey_version_concept_id,
    answer.survey_version_name
FROM `{dataset}.ds_survey` answer
WHERE answer.question_concept_id IN (1586134, 1585855)
  AND {where_clause}
"""


def extract_generated_exports(dataset: str | None = None) -> dict[str, pd.DataFrame]:
    dataset = dataset or require_workspace_cdr()
    extracts: dict[str, pd.DataFrame] = {"person": run_query(generated_person_sql(dataset))}
    for spec in GENERATED_DOMAIN_SPECS:
        extracts[spec.name] = run_query(generated_domain_sql(spec, dataset))
    extracts["survey"] = run_query(generated_survey_sql(dataset))
    return extracts


def quick_start(dataset: str | None = None) -> dict[str, pd.DataFrame]:
    """One-call notebook entrypoint: extract and print tables."""
    tables = extract_generated_exports(dataset)
    print_tables_fully(tables, max_rows=20)
    return tables


if __name__ == "__main__":
    print("Loaded spine_notebook_fixed.py (single copy/paste file).")
