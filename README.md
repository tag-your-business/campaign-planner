# campaign-planner
Create fully automated managed by AI campaign for the businesses

## Pre-commit checks

This repository uses `pre-commit` to run the following checks before commits and inside GitHub Actions:

- `check-ast`
- `check-case-conflict`
- `check-yaml`
- `check-json`
- `check-toml`
- `detect-aws-credentials`
- `detect-private-key`
- `trim-trailing-whitespace`
- `autoflake`
- `isort`
- `ruff`
- `black`

### Install locally

```bash
poetry install --with dev
poetry run pre-commit install
```

### Run manually

```bash
poetry run pre-commit run --all-files
```
