# TFLite Model Contract and Parity Evidence

## Current model asset

| Field | Value |
| --- | --- |
| File | `app/src/main/assets/lokal_fp32.tflite` |
| Version | `sapikenal-jenis-sapi-mobilenetv3-contract-v2-fp32` |
| Architecture | MobileNetV3 six-class image classifier |
| Size | 12,382,316 bytes (11.808697 MiB) |
| SHA-256 | `cc1b9a74af5ef44a7dead8848d6c41795aef9399c76e647f434277867eb113d9` |

The filename is configured through `BuildConfig.MODEL_FILE_NAME`. The version is
configured through `BuildConfig.MODEL_VERSION` and is persisted with local
inference results. The backend counterpart is
`apps/backend/model/best.keras` with SHA-256
`0d92bc9afec8ce8b57f3637720720fb6530664b8c38391ecf3b380df614b8f65`.
The project assigns this contract version because authoritative training/export
version metadata is unavailable; the checksums identify the exact artifacts.

## Tensor and class contract

The production asset was inspected with the standard-library verifier at
`python scripts/verify_model_contract.py` and has this runtime contract:

| Tensor | Shape | Dtype | Count |
| --- | --- | --- | --- |
| Input | `[1, 224, 224, 3]` | `float32` | 1 |
| Output | `[1, 6]` | `float32` | 1 |

Output indices are a strict contract:

1. `0 = aceh`
2. `1 = bali`
3. `2 = limusin`
4. `3 = madura`
5. `4 = pasundan`
6. `5 = po`

`OfflineInferenceEngine` validates the tensor counts, exact shapes, and dtypes
before inference. It also validates that every output is finite, lies in
`[0, 1]`, and that the six probabilities sum to approximately `1`.

## Preprocessing

Both runtimes prepare RGB input at 224 × 224 pixels and write Float32 channel
values in the raw `[0, 255]` range. No `/255` scaling is applied: the Keras model
contains `Rescaling(scale=1/127.5, offset=-1.0)`, and the TFLite conversion
retains that internal operation. The Android client corrects EXIF orientation,
resizes bilinearly to 224 × 224, and encodes PNG losslessly. Both local
inference and backend upload consume that same PNG.

## Keras–TFLite parity

The accepted baseline in [`../../docs/model/parity.md`](../../docs/model/parity.md)
uses 13 real team-provided fixtures. All input tensors are identical, all
winner classes match, and the measured maximum score delta is
`0.000002233688736`. This is runtime-consistency evidence, not an accuracy or
production-readiness claim.

## Version traceability

When replacing the offline model, update the following as one coordinated
change:

- `app/src/main/assets/lokal_fp32.tflite`;
- `app/src/main/assets/model_metadata.json`;
- `BuildConfig.MODEL_VERSION`;
- backend `class_names.json` and model metadata;
- class order and preprocessing configuration; and
- this contract/parity evidence.

## Runtime scope

Android inference is an image-classification result. It always selects one of
the four supported types after a decodable image reaches the model; it does not
validate that an image contains a cow or provide a health assessment.
