"""Benchmark REST API and WebSocket prediction transports against one backend.

Run a server with ``BENCHMARK_ENABLED=true`` first, then execute this script from
``apps/backend``. The script writes raw observations and a reproducible summary;
it does not alter production endpoints or the Android application contract.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import math
import platform
import statistics
import sys
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
try:
    from datetime import UTC, datetime
except ImportError:
    from datetime import datetime, timezone

    UTC = timezone.utc
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx
import websockets


@dataclass(frozen=True)
class ImageFixture:
    """An immutable benchmark image and the metadata needed to reproduce it."""

    path: Path
    content_type: str
    payload: bytes
    sha256: str

    @property
    def size_bytes(self) -> int:
        return len(self.payload)


@dataclass(frozen=True)
class Observation:
    """One end-to-end benchmark observation."""

    scenario: str
    protocol: str
    iteration: int
    image_name: str
    payload_size_bytes: int
    total_ms: float
    server_processing_ms: float
    communication_estimate_ms: float
    connection_setup_ms: float | None
    success: bool
    error: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark equivalent REST and WebSocket SapiKenal transports."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--images",
        type=Path,
        nargs="+",
        required=True,
        help="JPEG, PNG, or WebP files sent identically through both transports.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--warmups", type=int, default=10)
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument(
        "--scenarios",
        nargs="+",
        choices=("echo", "single_prediction", "repeated_prediction"),
        default=("echo", "single_prediction", "repeated_prediction"),
    )
    return parser.parse_args()


def content_type_for(path: Path) -> str:
    content_types = {
        ".jpeg": "image/jpeg",
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    try:
        return content_types[path.suffix.lower()]
    except KeyError as exc:
        raise ValueError(f"Unsupported benchmark image extension: {path}") from exc


def load_fixtures(paths: Iterable[Path]) -> list[ImageFixture]:
    fixtures: list[ImageFixture] = []
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"Benchmark image does not exist: {path}")
        payload = path.read_bytes()
        if not payload:
            raise ValueError(f"Benchmark image is empty: {path}")
        fixtures.append(
            ImageFixture(
                path=path.resolve(),
                content_type=content_type_for(path),
                payload=payload,
                sha256=hashlib.sha256(payload).hexdigest(),
            )
        )
    return fixtures


def websocket_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("--base-url must start with http:// or https://")
    scheme = "wss" if parsed.scheme == "https" else "ws"
    base_path = parsed.path.rstrip("/")
    return urlunparse(
        parsed._replace(scheme=scheme, path=f"{base_path}/api/benchmark/ws")
    )


def percentile(values: list[float], percentage: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentage
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def decode_websocket_response(message: str | bytes) -> dict[str, Any]:
    """Decode and validate one JSON WebSocket response from the benchmark server."""
    if isinstance(message, bytes):
        message = message.decode("utf-8")
    try:
        response = json.loads(message)
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("WebSocket benchmark response is not valid JSON") from exc
    if not isinstance(response, dict):
        raise ValueError("WebSocket benchmark response must be a JSON object")
    return response


def record_observation(
    scenario: str,
    protocol: str,
    iteration: int,
    fixture: ImageFixture,
    total_ms: float,
    response: dict[str, Any],
    connection_setup_ms: float | None = None,
) -> Observation:
    success = response.get("status") == "success"
    benchmark = response.get("benchmark", {})
    raw_server_processing_ms = benchmark.get("server_processing_ms", 0.0)
    try:
        server_processing_ms = float(raw_server_processing_ms)
    except (TypeError, ValueError):
        server_processing_ms = 0.0
    return Observation(
        scenario=scenario,
        protocol=protocol,
        iteration=iteration,
        image_name=fixture.path.name,
        payload_size_bytes=fixture.size_bytes,
        total_ms=round(total_ms, 3),
        server_processing_ms=server_processing_ms,
        communication_estimate_ms=round(max(total_ms - server_processing_ms, 0.0), 3),
        connection_setup_ms=connection_setup_ms,
        success=success,
        error="" if success else str(response.get("message", "Unknown response error")),
    )


async def rest_exchange(
    client: httpx.AsyncClient,
    base_url: str,
    operation: str,
    fixture: ImageFixture,
) -> tuple[float, dict[str, Any]]:
    endpoint = (
        "/api/benchmark/predict" if operation == "predict" else "/api/benchmark/echo"
    )
    field_name = "image" if operation == "predict" else "payload"
    content_type = (
        fixture.content_type if operation == "predict" else "application/octet-stream"
    )
    started_at = time.perf_counter()
    response = await client.post(
        f"{base_url}{endpoint}",
        files={field_name: (fixture.path.name, fixture.payload, content_type)},
    )
    total_ms = (time.perf_counter() - started_at) * 1_000
    response.raise_for_status()
    return total_ms, response.json()


async def rest_single_exchange(
    base_url: str,
    operation: str,
    fixture: ImageFixture,
) -> tuple[float, dict[str, Any]]:
    """Run one REST exchange through a new client and HTTP connection."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        return await rest_exchange(client, base_url, operation, fixture)


async def websocket_exchange(
    connection: websockets.ClientConnection,
    operation: str,
    fixture: ImageFixture,
) -> tuple[float, dict[str, Any]]:
    metadata: dict[str, str] = {"operation": operation}
    if operation == "predict":
        metadata["content_type"] = fixture.content_type
    started_at = time.perf_counter()
    await connection.send(json.dumps(metadata))
    await connection.send(fixture.payload)
    response = decode_websocket_response(await connection.recv())
    total_ms = (time.perf_counter() - started_at) * 1_000
    return total_ms, response


def comparable_prediction_contract(response: dict[str, Any]) -> dict[str, Any]:
    """Return only deterministic fields shared by equivalent prediction requests.

    Processing and benchmark timing values are intentionally excluded because the
    REST and WebSocket requests execute at different moments. They remain raw
    benchmark measurements and must not cause a false contract mismatch.
    """
    if response.get("status") != "success":
        return {key: value for key, value in response.items() if key != "benchmark"}
    return {
        "status": response.get("status"),
        "prediction": response.get("prediction"),
        "model_info": response.get("model_info"),
    }


async def assert_equivalent_prediction_outputs(
    client: httpx.AsyncClient,
    ws_url: str,
    base_url: str,
    fixtures: list[ImageFixture],
) -> None:
    """Fail fast if transports do not return the same prediction contract."""
    async with websockets.connect(ws_url) as connection:
        for fixture in fixtures:
            _, rest = await rest_exchange(client, base_url, "predict", fixture)
            _, websocket = await websocket_exchange(connection, "predict", fixture)
            comparable_rest = comparable_prediction_contract(rest)
            comparable_websocket = comparable_prediction_contract(websocket)
            if comparable_rest != comparable_websocket:
                raise AssertionError(
                    f"Prediction contracts differ for {fixture.path.name}: "
                    f"REST={comparable_rest}, WebSocket={comparable_websocket}"
                )


async def warm_up(
    client: httpx.AsyncClient,
    ws_url: str,
    base_url: str,
    fixture: ImageFixture,
    warmups: int,
) -> None:
    async with websockets.connect(ws_url) as connection:
        for _ in range(warmups):
            await rest_exchange(client, base_url, "predict", fixture)
            await websocket_exchange(connection, "predict", fixture)


async def benchmark_echo(
    client: httpx.AsyncClient,
    ws_url: str,
    base_url: str,
    fixtures: list[ImageFixture],
    iterations: int,
) -> list[Observation]:
    observations: list[Observation] = []
    async with websockets.connect(ws_url) as connection:
        for iteration in range(1, iterations + 1):
            fixture = fixtures[(iteration - 1) % len(fixtures)]
            if iteration % 2:
                rest_total, rest_response = await rest_exchange(
                    client, base_url, "echo", fixture
                )
                websocket_total, websocket_response = await websocket_exchange(
                    connection, "echo", fixture
                )
            else:
                websocket_total, websocket_response = await websocket_exchange(
                    connection, "echo", fixture
                )
                rest_total, rest_response = await rest_exchange(
                    client, base_url, "echo", fixture
                )
            observations.extend(
                (
                    record_observation(
                        "echo",
                        "REST API",
                        iteration,
                        fixture,
                        rest_total,
                        rest_response,
                    ),
                    record_observation(
                        "echo",
                        "WebSocket",
                        iteration,
                        fixture,
                        websocket_total,
                        websocket_response,
                    ),
                )
            )
    return observations


async def single_websocket_prediction(
    ws_url: str,
    fixture: ImageFixture,
    iteration: int,
) -> Observation:
    """Measure one prediction on a new WebSocket session and its setup time."""
    connection_started_at = time.perf_counter()
    async with websockets.connect(ws_url) as connection:
        connection_setup_ms = (time.perf_counter() - connection_started_at) * 1_000
        exchange_started_at = time.perf_counter()
        await connection.send(
            json.dumps({"operation": "predict", "content_type": fixture.content_type})
        )
        await connection.send(fixture.payload)
        websocket_response = decode_websocket_response(await connection.recv())
        websocket_exchange_ms = (time.perf_counter() - exchange_started_at) * 1_000
    return record_observation(
        "single_prediction",
        "WebSocket",
        iteration,
        fixture,
        connection_setup_ms + websocket_exchange_ms,
        websocket_response,
        connection_setup_ms=round(connection_setup_ms, 3),
    )


async def benchmark_single_prediction(
    client: httpx.AsyncClient,
    ws_url: str,
    base_url: str,
    fixtures: list[ImageFixture],
    iterations: int,
) -> list[Observation]:
    """Compare one prediction per session, including WebSocket connection setup."""
    observations: list[Observation] = []
    for iteration in range(1, iterations + 1):
        fixture = fixtures[(iteration - 1) % len(fixtures)]

        if iteration % 2:
            rest_total, rest_response = await rest_single_exchange(
                base_url, "predict", fixture
            )
            rest_observation = record_observation(
                "single_prediction",
                "REST API",
                iteration,
                fixture,
                rest_total,
                rest_response,
            )
            websocket_observation = await single_websocket_prediction(
                ws_url, fixture, iteration
            )
        else:
            websocket_observation = await single_websocket_prediction(
                ws_url, fixture, iteration
            )
            rest_total, rest_response = await rest_single_exchange(
                base_url, "predict", fixture
            )
            rest_observation = record_observation(
                "single_prediction",
                "REST API",
                iteration,
                fixture,
                rest_total,
                rest_response,
            )
        observations.extend((rest_observation, websocket_observation))
    return observations


async def benchmark_repeated_prediction(
    client: httpx.AsyncClient,
    ws_url: str,
    base_url: str,
    fixtures: list[ImageFixture],
    iterations: int,
) -> list[Observation]:
    """Compare keep-alive HTTP with a persistent WebSocket connection."""
    observations: list[Observation] = []
    async with websockets.connect(ws_url) as connection:
        for iteration in range(1, iterations + 1):
            fixture = fixtures[(iteration - 1) % len(fixtures)]
            if iteration % 2:
                rest_total, rest_response = await rest_exchange(
                    client, base_url, "predict", fixture
                )
                websocket_total, websocket_response = await websocket_exchange(
                    connection, "predict", fixture
                )
            else:
                websocket_total, websocket_response = await websocket_exchange(
                    connection, "predict", fixture
                )
                rest_total, rest_response = await rest_exchange(
                    client, base_url, "predict", fixture
                )
            observations.extend(
                (
                    record_observation(
                        "repeated_prediction",
                        "REST API",
                        iteration,
                        fixture,
                        rest_total,
                        rest_response,
                    ),
                    record_observation(
                        "repeated_prediction",
                        "WebSocket",
                        iteration,
                        fixture,
                        websocket_total,
                        websocket_response,
                    ),
                )
            )
    return observations


def summarize(observations: list[Observation]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[Observation]] = {}
    for observation in observations:
        grouped.setdefault((observation.scenario, observation.protocol), []).append(
            observation
        )

    summaries: list[dict[str, Any]] = []
    for (scenario, protocol), rows in sorted(grouped.items()):
        successful = [row for row in rows if row.success]
        total_values = [row.total_ms for row in successful]
        processing_values = [row.server_processing_ms for row in successful]
        communication_values = [row.communication_estimate_ms for row in successful]
        connection_setup_values = [
            row.connection_setup_ms
            for row in successful
            if row.connection_setup_ms is not None
        ]
        elapsed_seconds = max(sum(total_values) / 1_000, 0.001)
        summaries.append(
            {
                "scenario": scenario,
                "protocol": protocol,
                "n": len(rows),
                "successful": len(successful),
                "failed": len(rows) - len(successful),
                "mean_ms": round(statistics.fmean(total_values), 3)
                if total_values
                else 0.0,
                "median_p50_ms": round(statistics.median(total_values), 3)
                if total_values
                else 0.0,
                "p95_ms": round(percentile(total_values, 0.95), 3),
                "stddev_ms": round(statistics.stdev(total_values), 3)
                if len(total_values) > 1
                else 0.0,
                "mean_server_processing_ms": round(
                    statistics.fmean(processing_values), 3
                )
                if processing_values
                else 0.0,
                "mean_communication_estimate_ms": round(
                    statistics.fmean(communication_values), 3
                )
                if communication_values
                else 0.0,
                "mean_connection_setup_ms": round(
                    statistics.fmean(connection_setup_values), 3
                )
                if connection_setup_values
                else None,
                "throughput_transactions_per_second": round(
                    len(successful) / elapsed_seconds, 3
                ),
            }
        )
    return summaries


def write_artifacts(
    output_dir: Path,
    fixtures: list[ImageFixture],
    observations: list[Observation],
    summaries: list[dict[str, Any]],
    args: argparse.Namespace,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "raw-observations.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=Observation.__dataclass_fields__)
        writer.writeheader()
        writer.writerows(asdict(row) for row in observations)

    (output_dir / "summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "arguments": {
            "base_url": args.base_url,
            "images": [str(path) for path in args.images],
            "output_dir": str(args.output_dir),
            "warmups": args.warmups,
            "iterations": args.iterations,
            "scenarios": list(args.scenarios),
        },
        "fixtures": [
            {
                "path": str(fixture.path),
                "content_type": fixture.content_type,
                "size_bytes": fixture.size_bytes,
                "sha256": fixture.sha256,
            }
            for fixture in fixtures
        ],
        "notes": [
            "REST uses a new HTTP client in single_prediction and one shared client in repeated_prediction and echo.",
            "WebSocket uses a new connection in single_prediction and remains persistent in repeated_prediction and echo.",
            "single_prediction includes WebSocket connection setup in total_ms and records it separately.",
            "communication_estimate_ms is total_ms minus server_processing_ms; it is not pure network latency.",
        ],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


async def run(args: argparse.Namespace) -> None:
    if args.warmups < 0:
        raise ValueError("--warmups must be zero or greater")
    if args.iterations < 30:
        raise ValueError("--iterations must be at least 30 to satisfy the PRD")

    fixtures = load_fixtures(args.images)
    base_url = args.base_url.rstrip("/")
    ws_url = websocket_url(base_url)
    async with httpx.AsyncClient(timeout=120.0) as client:
        await assert_equivalent_prediction_outputs(client, ws_url, base_url, fixtures)
        await warm_up(client, ws_url, base_url, fixtures[0], args.warmups)

        observations: list[Observation] = []
        if "echo" in args.scenarios:
            observations.extend(
                await benchmark_echo(
                    client, ws_url, base_url, fixtures, args.iterations
                )
            )
        if "single_prediction" in args.scenarios:
            observations.extend(
                await benchmark_single_prediction(
                    client, ws_url, base_url, fixtures, args.iterations
                )
            )
        if "repeated_prediction" in args.scenarios:
            observations.extend(
                await benchmark_repeated_prediction(
                    client, ws_url, base_url, fixtures, args.iterations
                )
            )

    summaries = summarize(observations)
    write_artifacts(args.output_dir, fixtures, observations, summaries, args)
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
