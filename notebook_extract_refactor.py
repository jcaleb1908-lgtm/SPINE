"""Refactored All of Us domain extract helpers for notebook use.

This module keeps the generated cohort logic but removes repeated copy/paste blocks
that often get entangled across notebook cells.
"""

from __future__ import annotations

import os
from textwrap import dedent

import pandas as pd


def get_workspace_cdr() -> str:
    cdr = os.environ.get("WORKSPACE_CDR", "").strip()
    if not cdr:
        raise EnvironmentError(
            "WORKSPACE_CDR is not set. Run this inside All of Us Workbench or set it explicitly."
        )
    return cdr


def cohort_filter_sql(cdr: str, person_alias: str) -> str:
    """Return the cohort filter used across all domain pulls."""
    return dedent(
        f"""
        {person_alias}.person_id IN (
            SELECT DISTINCT person_id
            FROM `{cdr}.cb_search_person` cb_search_person
            WHERE cb_search_person.person_id IN (
                SELECT person_id
                FROM `{cdr}.cb_search_person` p
                WHERE DATE_DIFF(CURRENT_DATE, dob, YEAR)
                      - IF(EXTRACT(MONTH FROM dob) * 100 + EXTRACT(DAY FROM dob)
                           > EXTRACT(MONTH FROM CURRENT_DATE) * 100 + EXTRACT(DAY FROM CURRENT_DATE), 1, 0)
                    BETWEEN 40 AND 65
                  AND NOT EXISTS (
                      SELECT 1
                      FROM `{cdr}.death` d
                      WHERE d.person_id = p.person_id
                  )
            )
            AND cb_search_person.person_id IN (
                SELECT criteria.person_id
                FROM (
                    SELECT DISTINCT person_id, concept_id
                    FROM `{cdr}.cb_search_all_events`
                    WHERE concept_id IN (
                        SELECT DISTINCT c.concept_id
                        FROM `{cdr}.cb_criteria` c
                        JOIN (
                            SELECT CAST(cr.id AS STRING) AS id
                            FROM `{cdr}.cb_criteria` cr
                            WHERE concept_id IN (201826)
                              AND full_text LIKE '%_rank1]%'
                        ) a
                          ON (
                            c.path LIKE CONCAT('%.', a.id, '.%')
                            OR c.path LIKE CONCAT('%.', a.id)
                            OR c.path LIKE CONCAT(a.id, '.%')
                            OR c.path = a.id
                          )
                        WHERE is_standard = 1 AND is_selectable = 1
                    )
                    AND is_standard = 1
                ) criteria
            )
            AND cb_search_person.person_id IN (
                SELECT DISTINCT person_id
                FROM `{cdr}.cb_search_all_events`
                WHERE concept_id IN (903124) AND is_standard = 0
            )
            AND cb_search_person.person_id NOT IN (
                SELECT criteria.person_id
                FROM (
                    SELECT DISTINCT person_id, concept_id
                    FROM `{cdr}.cb_search_all_events`
                    WHERE concept_id IN (
                        SELECT DISTINCT c.concept_id
                        FROM `{cdr}.cb_criteria` c
                        JOIN (
                            SELECT CAST(cr.id AS STRING) AS id
                            FROM `{cdr}.cb_criteria` cr
                            WHERE concept_id IN (24612, 313217, 199074)
                              AND full_text LIKE '%_rank1]%'
                        ) a
                          ON (
                            c.path LIKE CONCAT('%.', a.id, '.%')
                            OR c.path LIKE CONCAT('%.', a.id)
                            OR c.path LIKE CONCAT(a.id, '.%')
                            OR c.path = a.id
                          )
                        WHERE is_standard = 1 AND is_selectable = 1
                    )
                    AND is_standard = 1
                ) criteria
            )
            AND cb_search_person.person_id NOT IN (
                SELECT person_id FROM `{cdr}.person` WHERE ethnicity_concept_id IN (903096, 0, 903079, 1586148)
                UNION DISTINCT
                SELECT person_id FROM `{cdr}.person` WHERE race_concept_id IN (2100000001, 903096, 45882607, 1177221)
                UNION DISTINCT
                SELECT person_id FROM `{cdr}.person` WHERE gender_concept_id IN (2000000002, 0)
                UNION DISTINCT
                SELECT person_id FROM `{cdr}.person` WHERE sex_at_birth_concept_id IN (2000000009, 0)
            )
        )
        """
    ).strip()


def run_query(sql: str) -> pd.DataFrame:
    return pd.read_gbq(
        sql,
        dialect="standard",
        use_bqstorage_api=("BIGQUERY_STORAGE_API_ENABLED" in os.environ),
        progress_bar_type="tqdm_notebook",
    )


def extract_person() -> pd.DataFrame:
    cdr = get_workspace_cdr()
    person_filter = cohort_filter_sql(cdr, "person")
    sql = f"""
    SELECT
        person.person_id,
        person.gender_concept_id,
        g.concept_name AS gender,
        person.birth_datetime AS date_of_birth,
        person.race_concept_id,
        r.concept_name AS race,
        person.ethnicity_concept_id,
        e.concept_name AS ethnicity,
        person.sex_at_birth_concept_id,
        s.concept_name AS sex_at_birth,
        person.self_reported_category_concept_id,
        c.concept_name AS self_reported_category
    FROM `{cdr}.person` person
    LEFT JOIN `{cdr}.concept` g ON person.gender_concept_id = g.concept_id
    LEFT JOIN `{cdr}.concept` r ON person.race_concept_id = r.concept_id
    LEFT JOIN `{cdr}.concept` e ON person.ethnicity_concept_id = e.concept_id
    LEFT JOIN `{cdr}.concept` s ON person.sex_at_birth_concept_id = s.concept_id
    LEFT JOIN `{cdr}.concept` c ON person.self_reported_category_concept_id = c.concept_id
    WHERE {person_filter}
    """
    return run_query(sql)


def extract_domain(domain: str, concept_ids: list[int], datetime_col: str) -> pd.DataFrame:
    """Generic helper for condition/drug/measurement pulls."""
    cdr = get_workspace_cdr()
    if domain not in {"condition_occurrence", "drug_exposure", "measurement"}:
        raise ValueError("domain must be one of: condition_occurrence, drug_exposure, measurement")

    alias = "x"
    concept_col = {
        "condition_occurrence": "condition_concept_id",
        "drug_exposure": "drug_concept_id",
        "measurement": "measurement_concept_id",
    }[domain]
    person_filter = cohort_filter_sql(cdr, alias)
    concept_list = ", ".join(str(i) for i in concept_ids)
    sql = f"""
    SELECT *
    FROM `{cdr}.{domain}` {alias}
    WHERE {alias}.{concept_col} IN ({concept_list})
      AND {person_filter}
      AND {alias}.{datetime_col} IS NOT NULL
    """
    return run_query(sql)


if __name__ == "__main__":
    # Minimal smoke test for notebook/script mode.
    df_person = extract_person()
    print("person rows:", len(df_person))
    print(df_person.head())
