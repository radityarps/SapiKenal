# Model files

The active SapiKenal model contract has seven outputs in this exact order:

```txt
0 = aceh
1 = bali
2 = limusin
3 = madura
4 = non_sapi
5 = pasundan
6 = po
```

The canonical class order is defined by `class_names.json` and is shared by
backend Keras inference and mobile TFLite inference. The model returns one of
the seven supported types (six cattle breeds or non_sapi) for every image that can be decoded.

## Production artifacts

| Runtime | Artifact | SHA-256 | Size |
| --- | --- | --- | ---: |
| Backend | `apps/backend/model/best.keras` | `231de918b6c4f821a76daea378eced59831666074edd71bf3c7dc8b9b8f5ba65` | 14,160,727 bytes |
| Mobile | `apps/mobile/app/src/main/assets/lokal_fp32.tflite` | `e083d87486d9f23e8b9ad732aecb5beaa71043cc573f8ad1b7c0be27966fcc4f` | 12,382,832 bytes |

Shared version: `sapikenal-jenis-sapi-mobilenetv3-contract-v2-fp32`. The
checksums above identify the exact supplied artifacts.

Both artifacts accept RGB `224 × 224` `float32` input in the raw `[0, 255]`
range and return seven `float32` probabilities in the canonical class order.
The Keras model contains `Rescaling(scale=1/127.5, offset=-1.0)` followed by a
seven-unit softmax output, so callers must not divide input values by 255.
Resize uses bilinear filtering. The Android client corrects EXIF orientation,
resizes to 224 × 224, and encodes PNG losslessly; backend model preprocessing
then converts RGB and adds the batch dimension without changing those pixels.

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
MODEL_VERSION=sapikenal-jenis-sapi-mobilenetv3-contract-v2-fp32
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
not run UI code or require TensorFlow. Real Keras–TFLite inference parity is a
separate device workflow documented in
[`../../../docs/model/parity.md`](../../../docs/model/parity.md). The accepted
baseline records identical input tensors, matching winners for 13 real
fixtures, and a measured maximum score delta of `0.000002233688736`.
