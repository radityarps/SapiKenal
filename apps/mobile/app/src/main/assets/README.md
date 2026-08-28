# Assets

The offline inference model lives in this folder.

Expected files:

- `cattle_disease.tflite` — selected MobileNetV3 Float32 TFLite artifact.
- `model_metadata.json` — model version, class order, preprocessing, size, and checksum.

Current model:

- Version: `cattle-disease-mobilenetv3-v20260725-fp32`
- Architecture: MobileNetV3 four-class classifier.
- Class order: `0 = FMD`, `1 = healthy`, `2 = LSD`, `3 = non_cattle`.
- Tensor input: `[1, 224, 224, 3]`, RGB, Float32 values in `[0, 255]`.
- Tensor output: `[1, 4]` Float32 probabilities in the same class order.
- Tensor preprocessing: no `/255` scaling because the model contains the MobileNetV3 internal rescaling layer.
- Client preprocessing: `ClientPreprocessor` applies available EXIF orientation before its client resize and JPEG stage.
- Asset size: `12,381,284` bytes.
- SHA-256: `ed9598c56b5dc5a5788c0d8376e8d6d2b80277aeca1931183f78cc968eae4bf9`.

Notes:

- Keep the exact `cattle_disease.tflite` filename because the application loads it through `BuildConfig.MODEL_FILE_NAME`.
- The Float32 artifact was produced from the final `tes1_best_v3.keras` training model and renamed for Android asset loading.
- `model_fp16 (1).tflite` is the alternative Float16 conversion artifact and is not loaded by the application.
- When replacing the offline model, update `model_metadata.json`, `MODEL_VERSION`, the class order, and preprocessing configuration together.
