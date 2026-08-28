# TFLite Model Contract and Parity Evidence

## Current model asset

| Field | Value |
| --- | --- |
| File | `app/src/main/assets/cattle_disease.tflite` |
| Version | `cattle-disease-mobilenetv3-v20260725-fp32` |
| Architecture | MobileNetV3 four-class classifier |
| Size | 12,381,284 bytes (11.8077125549 MiB) |
| SHA-256 | `ed9598c56b5dc5a5788c0d8376e8d6d2b80277aeca1931183f78cc968eae4bf9` |

The filename is configured through `BuildConfig.MODEL_FILE_NAME`. The version is
configured through `BuildConfig.MODEL_VERSION` and is persisted with local
inference results.

## Tensor and class contract

The current asset was inspected independently and has the following runtime
contract:

| Tensor | Shape | Dtype | Count |
| --- | --- | --- | --- |
| Input | `[1, 224, 224, 3]` | `float32` | 1 |
| Output | `[1, 4]` | `float32` | 1 |

Output indices are a strict contract:

1. `0 = FMD`
2. `1 = healthy`
3. `2 = LSD`
4. `3 = non_cattle`

`OfflineInferenceEngine` validates the tensor counts, exact shapes, and dtypes
before inference. It also validates that every output is finite, lies in
`[0, 1]`, and that the four probabilities sum to approximately `1`.

## Preprocessing

The application prepares RGB input at 224 × 224 pixels and writes Float32
channel values in the `[0, 255]` range. No `/255` scaling is applied because the
MobileNetV3 model contains its internal rescaling layer. The client corrects
available EXIF orientation before resizing and JPEG processing.

## Keras–TFLite parity

Parity evaluation must use the same held-out images for the final Keras model
and the deployed Float32 TensorFlow Lite model. Both paths must use the same RGB
conversion, 224 × 224 resize, Float32 input range, and class order.

The comparison should cover:

- tensor contract compatibility;
- top-class agreement;
- output-score difference;
- accuracy difference;
- macro F1-score difference; and
- per-class F1-score difference.

The repository snapshot records the current asset checksum and tensor-contract
smoke evidence above. It does not retain numerical accuracy or F1 parity deltas;
old three-class measurements must not be reused for this four-class asset.

## Version traceability

When replacing the offline model, update the following as one coordinated
change:

- `app/src/main/assets/cattle_disease.tflite`;
- `app/src/main/assets/model_metadata.json`;
- `BuildConfig.MODEL_VERSION`;
- class order and preprocessing configuration; and
- this contract/parity evidence.

## Runtime scope

Android inference is a local image-classification result for early detection. It
is not a clinical diagnosis and does not replace a veterinarian.
