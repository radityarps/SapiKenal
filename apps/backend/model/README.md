# Model files

The active SapiKenal model contract has six outputs in this exact order:

```txt
0 = aceh
1 = bali
2 = limusin
3 = madura
4 = pasundan
5 = po
```

The canonical class order is defined by `class_names.json` and is shared by
backend Keras inference and mobile TFLite inference. The model returns one of
the six supported types for every image that can be decoded; it does not
validate that the image contains a cow.

## Production artifacts

| Runtime | Artifact | SHA-256 | Size |
| --- | --- | --- | ---: |
| Backend | `apps/backend/model/best.keras` | `0d92bc9afec8ce8b57f3637720720fb6530664b8c38391ecf3b380df614b8f65` | 14,159,179 bytes |
| Mobile | `apps/mobile/app/src/main/assets/lokal_fp32.tflite` | `cc1b9a74af5ef44a7dead8848d6c41795aef9399c76e647f434277867eb113d9` | 12,382,316 bytes |

Shared version: `sapikenal-jenis-sapi-mobilenetv3-contract-v2-fp32`. The
checksums above identify the exact supplied artifacts.

Both artifacts accept RGB `224 × 224` `float32` input in the raw `[0, 255]`
range and return six `float32` probabilities in the canonical class order.
The Keras model contains `Rescaling(scale=1/127.5, offset=-1.0)` followed by a
six-unit softmax output, so callers must not divide input values by 255.
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
