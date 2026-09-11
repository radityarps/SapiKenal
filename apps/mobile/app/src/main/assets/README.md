# Model assets

SapiKenal's offline inference model is `lokal_fp32.tflite`. The matching
contract metadata is in `model_metadata.json`.

| Field | Value |
| --- | --- |
| Version | `sapikenal-jenis-sapi-mobilenetv3-contract-v2-fp32` |
| Architecture | MobileNetV3 six-class image classifier |
| Class order | `aceh`, `bali`, `limusin`, `madura`, `pasundan`, `po` |
| Input | RGB `224 × 224`, Float32 values in `[0, 255]` |
| Output | Six Float32 probabilities in the same class order |
| Size | 12,382,316 bytes |
| SHA-256 | `cc1b9a74af5ef44a7dead8848d6c41795aef9399c76e647f434277867eb113d9` |

The model contains an internal rescaling operation
`(input / 127.5) - 1.0`; therefore `ModelPreprocessor` must pass raw pixel
values and must not apply `/255` scaling. `ClientPreprocessor` corrects EXIF
orientation, resizes bilinearly to 224 × 224, and encodes PNG losslessly before
both local inference and upload.

The backend counterpart is `apps/backend/model/best.keras` with the same
version, class order, tensor contract, and documented checksum. The accepted
production parity baseline has identical input tensors and matching winners;
see [`../../../../../../docs/model/parity.md`](../../../../../../docs/model/parity.md).
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
