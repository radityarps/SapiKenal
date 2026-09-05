# Model files

The active SapiKenal model contract has four outputs in this exact order:

```txt
0 = bali
1 = brahman
2 = brangus
3 = limusin
```

The canonical class order is defined by `class_names.json` and is shared by
backend Keras inference and mobile TFLite inference. The model returns one of
the four supported types for every image that can be decoded; it does not
validate that the image contains a cow.

## Production artifacts

| Runtime | Artifact | SHA-256 | Size |
| --- | --- | --- | ---: |
| Backend | `apps/backend/model/best.keras` | `873c54eac9b4cf127ad29486ba6de3d4d0d16d415a3431aa7baa7e46d455434b` | 14,156,083 bytes |
| Mobile | `apps/mobile/app/src/main/assets/jenis_fp32.tflite` | `7b71a5a923ae69cf00b390712381c8d437d31e105e1370b0dc2653ba2271a664` | 12,381,284 bytes |

Shared version: `sapikenal-jenis-sapi-mobilenetv3-contract-v1-fp32`. This is a
project-assigned contract version because authoritative training/export version
metadata is unavailable; the checksums above identify the exact artifacts.

Both artifacts accept RGB `224 × 224` `float32` input in the raw `[0, 255]`
range and return four `float32` probabilities in the canonical class order.
The Keras model contains `Rescaling(scale=1/127.5, offset=-1.0)` followed by a
four-unit softmax output, so callers must not divide input values by 255.
Resize uses bilinear filtering. EXIF orientation is corrected before the
client resize/compression stage; model preprocessing itself only converts RGB,
resizes to 224 × 224, and adds the batch dimension.

The complete metadata and checksums are stored in
`apps/mobile/app/src/main/assets/model_metadata.json`.

## Registry and fallback

Model artifacts are private and are not committed through the Web Admin
registry workflow:

1. Upload one `.keras` artifact.
2. Wait for backend validation and `available` status.
3. Activate it separately with an operational reason.

Registry metadata records when a model was registered and activated. When an
active model is replaced, `deactivated_at` is recorded; when a retired model
is restored, `rolled_back_at` is recorded. These lifecycle timestamps are
introduced by Alembic migration `0004_model_lifecycle_timestamps` and are shown
in Web Admin model detail.

The checked-in `best.keras` can be used only as an explicitly enabled startup
fallback in a development or controlled environment:

```txt
MODEL_PATH=./model/best.keras
MODEL_CLASS_NAMES_PATH=./model/class_names.json
MODEL_VERSION=sapikenal-jenis-sapi-mobilenetv3-contract-v1-fp32
MODEL_STARTUP_FALLBACK_ENABLED=true
```

Without an active registry row or explicit fallback, `/api/health` is
`degraded` and `/api/predict` returns `503`.

## Verification

Run this from the repository root:

```bash
python scripts/verify_model_contract.py
```

The verifier checks class order, Keras archive structure and preprocessing,
TFLite FlatBuffer tensor shape/type/count, source defaults, metadata, artifact
sizes, and SHA-256 checksums. It uses Python's standard library only and does
not run UI code or require TensorFlow.
