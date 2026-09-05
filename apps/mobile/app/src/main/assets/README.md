# Model assets

SapiKenal's offline inference model is `jenis_fp32.tflite`. The matching
contract metadata is in `model_metadata.json`.

| Field | Value |
| --- | --- |
| Version | `sapikenal-jenis-sapi-mobilenetv3-contract-v1-fp32` |
| Architecture | MobileNetV3 four-class image classifier |
| Class order | `bali`, `brahman`, `brangus`, `limusin` |
| Input | RGB `224 × 224`, Float32 values in `[0, 255]` |
| Output | Four Float32 probabilities in the same class order |
| Size | 12,381,284 bytes |
| SHA-256 | `7b71a5a923ae69cf00b390712381c8d437d31e105e1370b0dc2653ba2271a664` |

The model contains an internal rescaling operation
`(input / 127.5) - 1.0`; therefore `ModelPreprocessor` must pass raw pixel
values and must not apply `/255` scaling. Input resizing uses bilinear
filtering. `ClientPreprocessor` corrects available EXIF orientation before its
client resize and JPEG compression.

The backend counterpart is `apps/backend/model/best.keras` with the same
version, class order, tensor contract, preprocessing, and documented checksum.
The project assigns this contract version because authoritative training/export
version metadata is unavailable; the checksums identify the exact artifacts.

When replacing this asset, update `model_metadata.json`, `BuildConfig.MODEL_FILE_NAME`,
`BuildConfig.MODEL_VERSION`, the backend model contract, and the verification
output together. Run from the repository root:

```bash
python scripts/verify_model_contract.py
```

The verifier uses only Python's standard library and rejects mismatched class
order, tensor contract, preprocessing metadata, model path, size, or checksum.
