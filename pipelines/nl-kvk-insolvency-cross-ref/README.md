# nl-kvk-insolvency-cross-ref

Cross-reference KVK company register with Centraal Insolventieregister to detect
rapid insolvencies and potential phoenix company patterns.

## Requirements

```
pip install -r requirements.txt
```

## Run

```bash
python3 pipelines/nl-kvk-insolvency-cross-ref/analyze.py
```

Outputs are written to `pipelines/nl-kvk-insolvency-cross-ref/output/`.
