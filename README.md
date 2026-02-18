# SPINE

Project 6 spine analysis pipeline.

## Notebook-safe generated export helpers (inside `spine`)

To avoid entangled copy/paste SQL cells, use these functions from the `spine` script:

- `cohort_filter_sql_for_generated_exports(dataset, person_alias)`
- `generated_person_sql(dataset)`
- `generated_domain_sql(spec, dataset)`
- `generated_survey_sql(dataset)`
- `extract_generated_exports(dataset)`
- `preview_generated_exports(extracts, rows=5)`

These are designed for All of Us Workbench notebook workflows and return pandas DataFrames
that are easy to print/copy.
