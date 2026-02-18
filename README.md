# SPINE

Utilities for Project 6 (degenerative spine disease + diabetes medications).

## Notebook extraction helper

Use `notebook_extract_refactor.py` when generated All of Us SQL cells become duplicated/entangled.
It keeps one shared cohort filter and provides reusable extract helpers:

- `extract_person()`
- `extract_domain(domain, concept_ids, datetime_col)` for `condition_occurrence`, `drug_exposure`, `measurement`

This is intended for copy/paste adaptation inside the All of Us Workbench Jupyter environment.
