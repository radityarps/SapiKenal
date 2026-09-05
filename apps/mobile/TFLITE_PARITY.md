# TFLite Model Contract and Parity Evidence

## Current model asset

| Field | Value |
| --- | --- |
| File | `app/src/main/assets/jenis_fp32.tflite` |
| Version | `sapikenal-jenis-sapi-mobilenetv3-contract-v1-fp32` |
| Architecture | MobileNetV3 four-class image classifier |
| Size | 12,381,284 bytes (11.8077125549 MiB) |
| SHA-256 | `7b71a5a923ae69cf00b390712381c8d437d31e105e1370b0dc2653ba2271a664` |

The filename is configured through `BuildConfig.MODEL_FILE_NAME`. The version is
configured through `BuildConfig.MODEL_VERSION` and is persisted with local
inference results. The backend counterpart is
`apps/backend/model/best.keras` with SHA-256
`873c54eac9b4cf127ad29486ba6de3d4d0d16d415a3431aa7baa7e46d455434b`.
The project assigns this contract version because authoritative training/export
version metadata is unavailable; the checksums identify the exact artifacts.

## Tensor and class contract

The production asset was inspected with the standard-library verifier at
`python scripts/verify_model_contract.py` and has this runtime contract:

| Tensor | Shape | Dtype | Count |
| --- | --- | --- | --- |
| Input | `[1, 224, 224, 3]` | `float32` | 1 |
| Output | `[1, 4]` | `float32` | 1 |

Output indices are a strict contract:

1. `0 = bali`
2. `1 = brahman`
3. `2 = brangus`
4. `3 = limusin`

`OfflineInferenceEngine` validates the tensor counts, exact shapes, and dtypes
before inference. It also validates that every output is finite, lies in
`[0, 1]`, and that the four probabilities sum to approximately `1`.

## Preprocessing

Both runtimes prepare RGB input at 224 × 224 pixels and write Float32 channel
values in the raw `[0, 255]` range. No `/255` scaling is applied: the Keras model
contains `Rescaling(scale=1/127.5, offset=-1.0)`, and the TFLite conversion
retains that internal operation. Resize uses bilinear filtering. The client
corrects available EXIF orientation before its resize and JPEG compression.

## Keras–TFLite parity

Issue 001 establishes the shared tensor and preprocessing contract only. A
numerical parity baseline requires an agreed held-out image corpus and is
tracked by the later parity issue. This document intentionally makes no
accuracy, F1, or top-class agreement claim until that corpus is measured.

## Version traceability

When replacing the offline model, update the following as one coordinated
change:

- `app/src/main/assets/jenis_fp32.tflite`;
- `app/src/main/assets/model_metadata.json`;
- `BuildConfig.MODEL_VERSION`;
- backend `class_names.json` and model metadata;
- class order and preprocessing configuration; and
- this contract/parity evidence.

## Runtime scope

Android inference is an image-classification result. It always selects one of
the four supported types after a decodable image reaches the model; it does not
validate that an image contains a cow or provide a health assessment.
