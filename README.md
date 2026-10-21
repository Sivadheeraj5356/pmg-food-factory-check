# PMG Food Factory Check

A small Django validation project for PMG Engineering's food-factory software context. It checks ingredient lots, production batches, and quality results before a batch is released.

The project is intentionally compact and auditable: it demonstrates Django forms, cross-field validation, service logic, and tests around a real manufacturing workflow.

## What it checks

- Ingredient lot quantities must be positive.
- Expiry cannot be before receipt.
- A production batch cannot use an ingredient lot after that lot expires.
- A batch is blocked when required quality checks are missing or failed.
- A batch is blocked when the planned quantity exceeds the available lot quantity.
- Quality-check temperatures must stay within a sane food-production range.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m unittest -v
```

Expected result: all tests pass.
