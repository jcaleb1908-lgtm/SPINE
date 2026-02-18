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
- `print_tables_fully(tables, max_rows=None, max_cols=None, max_colwidth=None)`

These are designed for All of Us Workbench notebook workflows and return pandas DataFrames
that are easy to print/copy.

### If your notebook says `NameError: print_tables_fully is not defined`
Run this one-cell fallback in the notebook:

```python
import pandas as pd

def print_tables_fully(tables, max_rows=None, max_cols=None, max_colwidth=None):
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
```

## Clean notebook file

If you want a fresh standalone notebook-safe version, use `spine_notebook_fixed.py`.
It includes:
- `print_tables_fully(...)`
- `strip_git_conflict_markers(...)`
- generated extract helpers and `extract_generated_exports(...)`
