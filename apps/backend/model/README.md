# Model files

The active model contract has four outputs in this exact order:

```txt
0 = FMD
1 = healthy
2 = LSD
3 = non_cattle
```

`non_cattle` is an input rejection class, not a disease. It produces the
`NON_CATTLE_IMAGE` domain error and must not be treated as a disease result.

Model artifacts are private and are not committed. The operational path is the
registry managed from Web Admin `/models`:

1. Upload one `.keras` artifact.
2. Wait for backend validation and `available` status.
3. Activate it separately with an operational reason.

Registry metadata records when a model was registered and activated. When an active model is replaced, `deactivated_at` is recorded; when a retired model is restored, `rolled_back_at` is recorded. These lifecycle timestamps are introduced by Alembic migration `0004_model_lifecycle_timestamps` and are shown in the Web Admin model detail. Prediction outcome and four-score fields are introduced by migration `0005_four_class_prediction_contract`.

The legacy `MODEL_PATH` file can be used only as an explicit startup fallback:

```txt
MODEL_PATH=./model/v2/tes1_best_v3.keras
MODEL_CLASS_NAMES_PATH=./model/class_names.json
MODEL_STARTUP_FALLBACK_ENABLED=true
```

Without an active registry row or explicit fallback, `/api/health` is
`degraded` and `/api/predict` returns `503`.
