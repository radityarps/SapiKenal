"""Smoke-test the running backend with the checked-in production model artifact."""

from __future__ import annotations

import argparse
import json
import math
import mimetypes
import time
from http.client import HTTPConnection, HTTPSConnection
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

CLASSES = ("bali", "brahman", "brangus", "limusin")
DEFAULT_IMAGE = Path(__file__).resolve().parents[1] / "tests/assets/sapi sehat 1.jpg"


def _request_json(
    url: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, object]]:
    parsed_url = urlparse(url)
    if (
        parsed_url.scheme not in {"http", "https"}
        or not parsed_url.netloc
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.hostname is None
    ):
        raise ValueError("Smoke-test URL must use an http or https URL")
    try:
        port = parsed_url.port
    except ValueError as exc:
        raise ValueError("Smoke-test URL has an invalid port") from exc

    connection_type = (
        HTTPSConnection if parsed_url.scheme == "https" else HTTPConnection
    )
    connection = connection_type(parsed_url.hostname, port=port, timeout=10)
    target = parsed_url.path or "/"
    if parsed_url.query:
        target += f"?{parsed_url.query}"
    try:
        connection.request(method, target, body=body, headers=headers or {})
        response = connection.getresponse()
        response_status = response.status
        raw_body = response.read()
    except OSError as exc:
        raise ConnectionError("Backend is unreachable") from exc
    finally:
        connection.close()

    if response_status >= 400:
        detail = raw_body.decode("utf-8", errors="replace")[:256]
        raise ValueError(f"HTTP {response_status}: {detail}")
    try:
        parsed_body = json.loads(raw_body)
    except (TypeError, ValueError) as exc:
        raise ValueError("Backend returned invalid JSON") from exc
    if not isinstance(parsed_body, dict):
        raise TypeError("Backend returned a non-object JSON response")
    return response_status, cast(dict[str, object], parsed_body)


def _wait_for_ready(base_url: str, wait_seconds: int) -> dict[str, object]:
    deadline = time.monotonic() + wait_seconds
    last_status = "unknown"
    health_url = f"{base_url}/api/health"
    while time.monotonic() < deadline:
        try:
            _, health = _request_json(health_url)
            last_status = (
                f"{health.get('status')} model_loaded={health.get('model_loaded')}"
            )
            if health.get("status") == "ok" and bool(health.get("model_loaded")):
                return health
        except (ConnectionError, TimeoutError, TypeError, ValueError) as exc:
            last_status = str(exc)
        time.sleep(1)
    raise TimeoutError(f"Backend did not become ready: {last_status}")


def _multipart_payload(image_path: Path) -> tuple[bytes, dict[str, str]]:
    boundary = "----SapiKenalProductionSmoke"
    content_type = (
        mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    )
    try:
        image_bytes = image_path.read_bytes()
    except OSError as exc:
        raise OSError(f"Fixture image could not be read: {image_path}") from exc
    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="{image_path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
        + image_bytes
        + f"\r\n--{boundary}--\r\n".encode()
    )
    return body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def _validate_prediction(response: dict[str, object]) -> tuple[str, float]:
    if response.get("status") != "success":
        raise ValueError("/api/predict did not return status=success")
    prediction_value = response.get("prediction")
    if not isinstance(prediction_value, dict):
        raise TypeError("/api/predict returned an unexpected prediction contract")
    prediction = cast(dict[str, object], prediction_value)
    if set(prediction) != {"predicted_class", "confidence", "scores"}:
        raise TypeError("/api/predict returned an unexpected prediction contract")

    predicted_class = prediction.get("predicted_class")
    scores_value = prediction.get("scores")
    confidence_value = prediction.get("confidence")
    if not isinstance(predicted_class, str) or predicted_class not in CLASSES:
        raise ValueError("/api/predict returned an invalid class contract")
    if not isinstance(scores_value, dict):
        raise TypeError("/api/predict returned invalid scores")
    if not isinstance(confidence_value, (int, float)) or isinstance(
        confidence_value, bool
    ):
        raise TypeError("/api/predict returned invalid confidence")
    scores = cast(dict[str, object], scores_value)
    if list(scores) != list(CLASSES):
        raise ValueError("/api/predict scores are not in canonical class order")

    numeric_scores: list[int | float] = []
    for value in scores.values():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError("/api/predict returned non-numeric scores")
        numeric_scores.append(value)
    try:
        values = [float(value) for value in numeric_scores]
        confidence = float(confidence_value)
    except (TypeError, ValueError) as exc:
        raise ValueError("/api/predict returned non-numeric scores") from exc
    top_index = max(range(len(values)), key=values.__getitem__)
    if (
        not all(math.isfinite(value) and 0 <= value <= 1 for value in values)
        or not math.isclose(sum(values), 1.0, abs_tol=0.01)
        or not math.isfinite(confidence)
        or predicted_class != CLASSES[top_index]
        or not math.isclose(confidence, values[top_index], abs_tol=0.01)
    ):
        raise ValueError("/api/predict returned invalid probabilities")
    return predicted_class, confidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--wait-seconds", type=int, default=90)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    parsed_url = urlparse(base_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("--base-url must use an http or https URL")
    if not args.image.is_file():
        raise FileNotFoundError(f"Fixture image not found: {args.image}")

    health = _wait_for_ready(base_url, args.wait_seconds)
    body, headers = _multipart_payload(args.image)
    _, response = _request_json(
        f"{base_url}/api/predict",
        method="POST",
        body=body,
        headers=headers,
    )
    predicted_class, confidence = _validate_prediction(response)
    print(
        "SMOKE OK "
        f"model_version={health.get('model_version')} "
        f"predicted_class={predicted_class} "
        f"confidence={confidence:.6f} scores={len(CLASSES)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
