#!/usr/bin/env python3
"""Measure captured Android production output against production Keras inference.

Run with backend dependencies and PYTHONPATH=apps/backend. Without --baseline,
this records measurements only, never a passing parity/release verdict.
"""

import argparse
import hashlib
import importlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLASSES = ["aceh", "bali", "limusin", "madura", "pasundan", "po"]


def validate_scores(scores):
    if (
        len(scores) != len(CLASSES)
        or any(not math.isfinite(v) or not 0 <= v <= 1 for v in scores)
        or abs(sum(scores) - 1) > 0.01
    ):
        raise ValueError(f"Expected {len(CLASSES)} finite probabilities summing to one")


def check_regression(report, baseline):
    failures = []
    if baseline.get("status") != "accepted":
        failures.append("Baseline is blocked or has not been explicitly accepted")
    if report["identity"] != baseline["identity"]:
        failures.append(
            "Corpus, model, or runtime identity changed; review a new baseline"
        )
    if not report["observations"]:
        failures.append("Empty capture")
    for row in report["observations"]:
        if not row["same_winner"]:
            failures.append(f"{row['id']}: winner mismatch; release blocked")
        if not row["input_equal"]:
            failures.append(
                f"{row['id']}: production preprocessing differs; release blocked"
            )
        for field, limit in [
            ("score_delta_max", "score_tolerance"),
            ("same_tensor_score_delta_max", "same_tensor_score_tolerance"),
            ("input_delta_max", "input_tolerance"),
        ]:
            value, tolerance = row[field], baseline[limit]
            if (
                not math.isfinite(tolerance)
                or tolerance < 0
                or not math.isfinite(value)
                or value > tolerance
            ):
                failures.append(f"{row['id']}: {field} exceeds measured {limit}")
    return failures


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read JSON {path}: {exc}") from exc


def finite_float(value, description):
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"Invalid {description}: {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"Non-finite {description}")
    return result


def measure(capture):
    import numpy as np  # pyright: ignore[reportMissingImports]
    import PIL  # pyright: ignore[reportMissingImports]
    import tensorflow as tf  # pyright: ignore[reportMissingModuleSource]
    from PIL import Image  # pyright: ignore[reportMissingImports]

    InferenceService = importlib.import_module("inference_server").InferenceService
    ModelPreprocessor = importlib.import_module(
        "preprocessing.model_preprocessor"
    ).ModelPreprocessor

    android = read_json(capture / "android.json")
    manifest = read_json(capture / "fixtures.json")
    metadata = read_json(ROOT / "apps/mobile/app/src/main/assets/model_metadata.json")
    keras_path = ROOT / "apps/backend/model/best.keras"
    keras_sha = digest(keras_path.read_bytes())
    expected = {
        "schema": 1,
        "class_order": CLASSES,
        "input_shape": [1, 224, 224, 3],
        "output_shape": [1, 6],
        "dtype": "float32",
        "byte_order": "LITTLE_ENDIAN",
        "model_version": metadata["model_version"],
        "model_sha256": metadata["sha256"],
    }
    if any(android.get(key) != value for key, value in expected.items()):
        raise ValueError("Android capture does not match the production model contract")
    if keras_sha != metadata["backend_artifact"]["sha256"]:
        raise ValueError("Keras artifact checksum mismatch")
    rows = android["observations"]
    if not rows or [r["id"] for r in rows] != [r["id"] for r in manifest]:
        raise ValueError("Missing, reordered, or extra fixtures")
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)) or any(
        not re.fullmatch(r"fixture-[0-9]+\.png", name) for name in ids
    ):
        raise ValueError("Unsafe or duplicate fixture IDs")
    if {Path(row["path"]).parts[0] for row in manifest} != set(CLASSES):
        raise ValueError("Corpus must cover the six canonical class folders")
    service = InferenceService(str(keras_path))
    observations = []
    for row, source in zip(rows, manifest, strict=True):
        name = row["id"]
        image_bytes = (capture / name).read_bytes()
        tensor = (capture / (name + ".f32")).read_bytes()
        if (
            row["source_sha256"] != source["sha256"]
            or digest(image_bytes) != row["image_sha256"]
            or digest(tensor) != row["tensor_sha256"]
        ):
            raise ValueError(f"Fixture/capture checksum mismatch: {name}")
        android_input = np.frombuffer(tensor, dtype="<f4").reshape(1, 224, 224, 3)
        if (
            not np.all(np.isfinite(android_input))
            or np.any(android_input < 0)
            or np.any(android_input > 255)
        ):
            raise ValueError(f"Invalid Android float32 RGB tensor: {name}")
        with Image.open(capture / name) as image:
            rgb = image.convert("RGB")
            backend_input = ModelPreprocessor.process(rgb)
            result = service.predict(rgb)
        if backend_input.shape != (1, 224, 224, 3) or backend_input.dtype != np.float32:
            raise ValueError("Backend input tensor contract mismatch")
        if (
            result["status"] != "success"
            or list(result["prediction"]["scores"]) != CLASSES
        ):
            raise ValueError(f"Backend inference failed or class order changed: {name}")
        keras_scores = list(result["prediction"]["scores"].values())
        lite_scores = row["scores"]
        validate_scores(keras_scores)
        validate_scores(lite_scores)
        if row["winner"] != CLASSES[max(range(4), key=lambda i: lite_scores[i])]:
            raise ValueError(f"Android winner does not match scores: {name}")
        # Diagnostic separation: model-export delta on the exact production tensor.
        same_tensor = np.asarray(service.model_loader.predict(android_input))
        if same_tensor.shape != (1, 4) or same_tensor.dtype != np.float32:
            raise ValueError("Keras output tensor contract mismatch")
        validate_scores(same_tensor[0].tolist())
        pixel_delta = np.abs(backend_input - android_input)
        observations.append(
            {
                "id": name,
                "source_sha256": source["sha256"],
                "keras_winner": result["prediction"]["predicted_class"],
                "tflite_winner": row["winner"],
                "same_winner": result["prediction"]["predicted_class"] == row["winner"],
                "keras_scores": keras_scores,
                "tflite_scores": lite_scores,
                "score_delta_max": finite_float(
                    np.max(np.abs(np.array(keras_scores) - lite_scores)), "score delta"
                ),
                "same_tensor_score_delta_max": finite_float(
                    np.max(np.abs(same_tensor[0] - lite_scores)),
                    "same-tensor score delta",
                ),
                "input_delta_max": finite_float(
                    pixel_delta.max(), "maximum input delta"
                ),
                "input_delta_mean": finite_float(
                    pixel_delta.mean(), "mean input delta"
                ),
                "input_equal": bool(np.array_equal(backend_input, android_input)),
            }
        )
    return {
        "schema": 1,
        "identity": {
            "keras_sha256": keras_sha,
            "tflite_sha256": android["model_sha256"],
            "model_version": android["model_version"],
            "class_order": CLASSES,
            "tensorflow": tf.__version__,
            "pillow": PIL.__version__,
            "numpy": np.__version__,
            "device": android["device"],
            "tflite_runtime": android["tflite_runtime"],
            "fixtures": [
                {"id": row["id"], "sha256": row["sha256"]} for row in manifest
            ],
        },
        "observations": observations,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    report = measure(args.capture)
    failures = []
    if args.baseline:
        failures = check_regression(report, read_json(args.baseline))
    report["verdict"] = (
        "MEASURED_ONLY" if not args.baseline else ("FAIL" if failures else "PASS")
    )
    report["failures"] = failures
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(report["verdict"], f"fixtures={len(report['observations'])}")
    for row in report["observations"]:
        print(
            row["id"],
            row["keras_winner"],
            row["tflite_winner"],
            f"score_delta={row['score_delta_max']:.9g}",
            f"pixel_delta={row['input_delta_max']:g}",
        )
    for failure in failures:
        print(failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
