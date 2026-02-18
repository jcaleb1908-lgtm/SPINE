# SPINE

## Single copy/paste notebook file

Use only this file:

- `spine_notebook_fixed.py`

It includes everything needed for notebook usage:
- cohort SQL helpers
- generated domain extract helpers
- `extract_generated_exports(...)`
- `print_tables_fully(...)`
- `strip_git_conflict_markers(...)`

Quick notebook usage:

```python
# after pasting spine_notebook_fixed.py into a notebook cell and running it
extracts = extract_generated_exports()   # uses WORKSPACE_CDR
print_tables_fully(extracts)
```
