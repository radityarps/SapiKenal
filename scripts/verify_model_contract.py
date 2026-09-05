#!/usr/bin/env python3
"""Validate the SapiKenal Keras/TFLite model contract without UI inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import sys
import zipfile
from pathlib import Path
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parents[1]
BACKEND_MODEL = ROOT / "apps/backend/model/best.keras"
BACKEND_CLASSES = ROOT / "apps/backend/model/class_names.json"
MOBILE_MODEL = ROOT / "apps/mobile/app/src/main/assets/jenis_fp32.tflite"
MOBILE_METADATA = ROOT / "apps/mobile/app/src/main/assets/model_metadata.json"

CLASSES = ["bali", "brahman", "brangus", "limusin"]
MODEL_VERSION = "sapikenal-jenis-sapi-mobilenetv3-contract-v1-fp32"
INPUT_SHAPE = [1, 224, 224, 3]
OUTPUT_SHAPE = [1, 4]
INPUT_DTYPE = "float32"
OUTPUT_DTYPE = "float32"
RESCALING_SCALE = 1 / 127.5
RESCALING_OFFSET = -1.0


class ContractError(ValueError):
    """A model contract check failed."""


def fail(message: str) -> NoReturn:
    raise ContractError(message)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Cannot read JSON {path.relative_to(ROOT)}: {exc}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        fail(f"Cannot read artifact {path.relative_to(ROOT)}: {exc}")
    return digest.hexdigest()


def require_file(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        fail(f"Artifact is missing or is a symlink: {path.relative_to(ROOT)}")


def dtype_name(value: Any) -> str | None:
    if isinstance(value, str):
        return value.removeprefix("tf.").casefold()
    if isinstance(value, dict):
        config = value.get("config")
        if isinstance(config, dict):
            name = config.get("name")
            if isinstance(name, str):
                return name.casefold()
    return None


def validate_class_names() -> None:
    data = read_json(BACKEND_CLASSES)
    if not isinstance(data, dict):
        fail("class_names.json must be a JSON object")
    expected_keys = {str(index) for index in range(len(CLASSES))}
    if set(data) != expected_keys:
        fail(f"class_names.json keys must be {sorted(expected_keys)}")
    actual = [data[str(index)] for index in range(len(CLASSES))]
    if actual != CLASSES:
        fail(f"class_names.json order is {actual}; expected {CLASSES}")
    print(f"PASS class order: {', '.join(CLASSES)}")


def require_float(value: Any, expected: float, description: str) -> None:
    try:
        actual = float(value)
    except (TypeError, ValueError):
        fail(f"{description} is not numeric: {value!r}")
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12):
        fail(f"{description} is {actual}; expected {expected}")


def validate_keras() -> dict[str, Any]:
    require_file(BACKEND_MODEL)
    config: Any
    try:
        with zipfile.ZipFile(BACKEND_MODEL) as archive:
            names = set(archive.namelist())
            if {"config.json", "model.weights.h5"} - names:
                fail("best.keras is missing config.json or model.weights.h5")
            config = json.loads(archive.read("config.json"))
    except (OSError, zipfile.BadZipFile, KeyError, json.JSONDecodeError) as exc:
        fail(f"Cannot inspect best.keras: {exc}")

    root = config.get("config")
    if not isinstance(root, dict):
        fail("best.keras has no readable Functional model config")
    layers = root.get("layers")
    if not isinstance(layers, list):
        fail("best.keras has no readable Functional model layers")

    input_layers = [
        layer for layer in layers if layer.get("class_name") == "InputLayer"
    ]
    if len(input_layers) != 1:
        fail("best.keras must contain exactly one InputLayer")
    input_config = input_layers[0].get("config", {})
    if input_config.get("batch_shape") != [None, 224, 224, 3]:
        fail(
            f"Keras input shape is {input_config.get('batch_shape')}; expected [None, 224, 224, 3]"
        )
    if dtype_name(input_config.get("dtype")) != INPUT_DTYPE:
        fail(f"Keras input dtype is {input_config.get('dtype')}; expected float32")

    rescaling_layers = [
        layer for layer in layers if layer.get("class_name") == "Rescaling"
    ]
    if len(rescaling_layers) != 1:
        fail("best.keras must contain exactly one Rescaling layer")
    rescaling = rescaling_layers[0].get("config", {})
    require_float(rescaling.get("scale"), RESCALING_SCALE, "Keras rescaling scale")
    require_float(rescaling.get("offset"), RESCALING_OFFSET, "Keras rescaling offset")

    output_layers = root.get("output_layers")
    if not isinstance(output_layers, list) or not output_layers:
        fail("best.keras has no output layer declaration")
    output_ref = output_layers[0]
    if isinstance(output_ref, str):
        output_name = output_ref
    elif isinstance(output_ref, list) and output_ref and isinstance(output_ref[0], str):
        output_name = output_ref[0]
    else:
        fail("best.keras has an invalid output layer declaration")
    output_candidates = [layer for layer in layers if layer.get("name") == output_name]
    if len(output_candidates) != 1:
        fail(f"Keras output layer {output_name!r} is not uniquely declared")
    output_config = output_candidates[0].get("config", {})
    if output_candidates[0].get("class_name") != "Dense":
        fail("Keras output layer must be Dense")
    if dtype_name(output_config.get("dtype")) != OUTPUT_DTYPE:
        fail(f"Keras output dtype is {output_config.get('dtype')}; expected float32")
    if (
        output_config.get("units") != len(CLASSES)
        or output_config.get("activation") != "softmax"
    ):
        fail("Keras output must be Dense(4, activation=softmax)")

    checksum = sha256(BACKEND_MODEL)
    size = BACKEND_MODEL.stat().st_size
    print(
        "PASS Keras tensor contract: input float32 [None, 224, 224, 3], "
        "output softmax float32 [None, 4]"
    )
    print(f"PASS Keras artifact: {size} bytes, sha256={checksum}")
    return {"sha256": checksum, "size_bytes": size}


class _Table:
    def __init__(self, data: bytes, position: int):
        self.data = data
        self.position = position
        self.vtable = position - _i32(data, position)
        self.vtable_size = _u16(data, self.vtable)

    def field(self, index: int) -> int:
        entry = self.vtable + 4 + index * 2
        if entry + 2 > self.vtable + self.vtable_size:
            return 0
        offset = _u16(self.data, entry)
        return self.position + offset if offset else 0


def _u16(data: bytes, position: int) -> int:
    return struct.unpack_from("<H", data, position)[0]


def _u32(data: bytes, position: int) -> int:
    return struct.unpack_from("<I", data, position)[0]


def _i32(data: bytes, position: int) -> int:
    return struct.unpack_from("<i", data, position)[0]


def _u8(data: bytes, position: int) -> int:
    return data[position]


def _root_table(data: bytes) -> _Table:
    root = _u32(data, 0)
    return _Table(data, root)


def _vector_start(data: bytes, table: _Table, field_index: int) -> int:
    field = table.field(field_index)
    if not field:
        return 0
    return field + _u32(data, field)


def _vector_length(data: bytes, vector: int) -> int:
    return _u32(data, vector)


def _vector_ints(data: bytes, table: _Table, field_index: int) -> list[int]:
    vector = _vector_start(data, table, field_index)
    if not vector:
        return []
    length = _vector_length(data, vector)
    return [_i32(data, vector + 4 + index * 4) for index in range(length)]


def _vector_tables(data: bytes, table: _Table, field_index: int) -> list[_Table]:
    vector = _vector_start(data, table, field_index)
    if not vector:
        return []
    length = _vector_length(data, vector)
    tables: list[_Table] = []
    for index in range(length):
        element = vector + 4 + index * 4
        tables.append(_Table(data, element + _u32(data, element)))
    return tables


def _string(data: bytes, table: _Table, field_index: int) -> str:
    field = table.field(field_index)
    if not field:
        return ""
    start = field + _u32(data, field)
    length = _u32(data, start)
    return data[start + 4 : start + 4 + length].decode("utf-8", errors="replace")


def _tensor_shape(data: bytes, tensor: _Table) -> list[int]:
    vector = _vector_start(data, tensor, 0)
    if not vector:
        return []
    length = _vector_length(data, vector)
    return [_i32(data, vector + 4 + index * 4) for index in range(length)]


def _scalar(data: bytes, table: _Table, field_index: int, default: int = -1) -> int:
    field = table.field(field_index)
    return default if not field else _u8(data, field)


def _tensor_type(data: bytes, tensor: _Table) -> int:
    """Read TensorType, whose FlatBuffer enum field is a byte at vtable slot 1."""
    field = tensor.field(1)
    if field:
        return _u8(data, field)
    # FlatBuffers omits fields equal to their schema default. TensorType.FLOAT32
    # is enum value 0, so an omitted field is also FLOAT32.
    return 0


def _operator_builtin_code(data: bytes, opcode: _Table) -> int:
    # OperatorCode.builtin_code is field 3 in the current schema; older
    # FlatBuffers stored the same enum in deprecated_builtin_code (field 0).
    field = opcode.field(3) or opcode.field(0)
    # Both schema fields default to ADD (enum value 0), so an omitted field
    # is valid for the ADD opcode.
    return _u8(data, field) if field else 0


def _operator_opcode_index(data: bytes, operator: _Table) -> int:
    field = operator.field(0)
    if not field:
        return 0
    return _u8(data, field)


def _tensor_buffer_index(data: bytes, tensor: _Table) -> int:
    field = tensor.field(2)
    return _u32(data, field) if field else 0


def _buffer_data(data: bytes, buffers: list[_Table], index: int) -> bytes:
    if not 0 <= index < len(buffers):
        fail(f"TFLite tensor references invalid buffer {index}")
    vector = _vector_start(data, buffers[index], 0)
    if not vector:
        return b""
    length = _vector_length(data, vector)
    end = vector + 4 + length
    if end > len(data):
        fail("TFLite buffer extends beyond the artifact")
    return data[vector + 4 : end]


def _scalar_float_buffer(
    data: bytes, buffers: list[_Table], tensor: _Table, description: str
) -> float:
    raw = _buffer_data(data, buffers, _tensor_buffer_index(data, tensor))
    if len(raw) != 4:
        fail(f"{description} must be one float32 constant")
    value = struct.unpack("<f", raw)[0]
    if not math.isfinite(value):
        fail(f"{description} must be finite")
    return value


def _validate_tflite_graph(data: bytes) -> tuple[list[int], list[int]]:
    if len(data) < 8 or data[4:8] != b"TFL3":
        fail("TFLite artifact has an invalid FlatBuffer identifier")
    try:
        root = _root_table(data)
        opcodes = _vector_tables(data, root, 1)
        subgraphs = _vector_tables(data, root, 2)
        buffers = _vector_tables(data, root, 4)
    except (IndexError, struct.error, UnicodeError, ValueError) as exc:
        fail(f"Cannot inspect TFLite FlatBuffer: {exc}")
    if len(subgraphs) != 1:
        fail(f"TFLite model must contain one subgraph; found {len(subgraphs)}")

    subgraph = subgraphs[0]
    tensors = _vector_tables(data, subgraph, 0)
    inputs = _vector_ints(data, subgraph, 1)
    outputs = _vector_ints(data, subgraph, 2)
    operators = _vector_tables(data, subgraph, 3)
    if len(inputs) != 1 or len(outputs) != 1:
        fail(
            f"TFLite tensor counts must be one input and one output; got {len(inputs)} and {len(outputs)}"
        )
    if not tensors or not all(0 <= index < len(tensors) for index in inputs + outputs):
        fail("TFLite subgraph references an invalid tensor")
    if not operators:
        fail("TFLite subgraph has no operators")

    input_tensor = tensors[inputs[0]]
    output_tensor = tensors[outputs[0]]
    input_shape = _tensor_shape(data, input_tensor)
    output_shape = _tensor_shape(data, output_tensor)
    if any(
        index < 0 or index >= len(tensors)
        for operator in operators
        for index in _vector_ints(data, operator, 1) + _vector_ints(data, operator, 2)
    ):
        fail("TFLite operator references an invalid tensor")
    input_type = _tensor_type(data, input_tensor)
    output_type = _tensor_type(data, output_tensor)
    # TensorType.FLOAT32 is 0 in the TensorFlow Lite schema.
    if input_shape != INPUT_SHAPE or input_type != 0:
        fail(
            f"TFLite input is shape={input_shape}, type={input_type}; expected {INPUT_SHAPE}, FLOAT32"
        )
    if output_shape != OUTPUT_SHAPE or output_type != 0:
        fail(
            f"TFLite output is shape={output_shape}, type={output_type}; expected {OUTPUT_SHAPE}, FLOAT32"
        )

    try:
        operator_indices = [
            _operator_opcode_index(data, operator) for operator in operators
        ]
    except (IndexError, struct.error, UnicodeError, ValueError) as exc:
        fail(f"Cannot inspect TFLite operator graph: {exc}")
    if not all(0 <= index < len(opcodes) for index in operator_indices):
        fail("TFLite operator references an invalid opcode")
    builtin_codes = [
        _operator_builtin_code(data, opcodes[index]) for index in operator_indices
    ]

    # Keras Rescaling(1/127.5, -1) is exported as MUL then ADD at the graph
    # boundary. Checking the constants and tensor chain catches callers that
    # only happen to preserve tensor shapes while changing preprocessing.
    if len(operators) < 2 or builtin_codes[:2] != [18, 0]:  # MUL, ADD
        fail("TFLite graph must begin with MUL then ADD for model rescaling")
    first_inputs = _vector_ints(data, operators[0], 1)
    first_outputs = _vector_ints(data, operators[0], 2)
    second_inputs = _vector_ints(data, operators[1], 1)
    second_outputs = _vector_ints(data, operators[1], 2)
    if (
        len(first_inputs) != 2
        or first_inputs[0] != inputs[0]
        or len(first_outputs) != 1
        or len(second_inputs) != 2
        or second_inputs[0] != first_outputs[0]
        or len(second_outputs) != 1
    ):
        fail("TFLite graph rescaling operators are not connected to the model input")
    scale_tensor_index = first_inputs[1] if len(first_inputs) > 1 else -1
    offset_tensor_index = second_inputs[1] if len(second_inputs) > 1 else -1
    if not 0 <= scale_tensor_index < len(tensors) or not 0 <= offset_tensor_index < len(
        tensors
    ):
        fail("TFLite graph rescaling constants reference invalid tensors")
    scale = _scalar_float_buffer(
        data, buffers, tensors[scale_tensor_index], "TFLite rescaling scale"
    )
    offset = _scalar_float_buffer(
        data, buffers, tensors[offset_tensor_index], "TFLite rescaling offset"
    )
    if not math.isclose(scale, RESCALING_SCALE, rel_tol=0, abs_tol=1e-7):
        fail(f"TFLite graph rescaling scale is {scale}; expected {RESCALING_SCALE}")
    if not math.isclose(offset, RESCALING_OFFSET, rel_tol=0, abs_tol=1e-7):
        fail(f"TFLite graph rescaling offset is {offset}; expected {RESCALING_OFFSET}")

    # The exported output must be the final SOFTMAX (BuiltinOperator 25), not
    # merely a four-value tensor that could contain logits.
    final_operator = operators[-1]
    if builtin_codes[-1] != 25:  # SOFTMAX
        fail("TFLite graph must end with a SOFTMAX operator")
    final_inputs = _vector_ints(data, final_operator, 1)
    final_outputs = _vector_ints(data, final_operator, 2)
    previous_outputs = _vector_ints(data, operators[-2], 2)
    if len(final_inputs) != 1 or final_inputs != previous_outputs:
        fail("TFLite SOFTMAX must consume the preceding logits tensor")
    if len(final_outputs) != 1 or final_outputs[0] != outputs[0]:
        fail("TFLite SOFTMAX must produce the declared model output")

    print(
        "PASS TFLite graph contract: raw [0, 255] input, "
        f"rescaling MUL {scale:g} then ADD {offset:g}, final softmax"
    )
    return input_shape, output_shape


def validate_tflite_bytes(data: bytes) -> None:
    """Validate a TFLite artifact from bytes, including its executable graph."""
    try:
        _validate_tflite_graph(data)
    except (IndexError, struct.error, UnicodeError, ValueError) as exc:
        if isinstance(exc, ContractError):
            raise
        fail(f"Cannot inspect TFLite FlatBuffer: {exc}")


def run_self_check() -> None:
    """Exercise both the valid graph path and malformed-contract rejection."""
    validate_tflite_bytes(MOBILE_MODEL.read_bytes())
    try:
        validate_tflite_bytes(b"not a TFLite model")
    except ContractError:
        print("PASS malformed TFLite contract is rejected")
    else:
        fail("Self-check accepted a malformed TFLite contract")


def validate_tflite() -> dict[str, Any]:
    require_file(MOBILE_MODEL)
    try:
        data = MOBILE_MODEL.read_bytes()
        input_shape, output_shape = _validate_tflite_graph(data)
    except (OSError, IndexError, struct.error, UnicodeError, ValueError) as exc:
        fail(f"Cannot inspect TFLite FlatBuffer: {exc}")

    checksum = sha256(MOBILE_MODEL)
    size = MOBILE_MODEL.stat().st_size
    print(
        f"PASS TFLite tensor contract: input float32 {input_shape}, output float32 {output_shape}"
    )
    print(f"PASS TFLite artifact: {size} bytes, sha256={checksum}")
    return {"sha256": checksum, "size_bytes": size}


def validate_metadata(keras: dict[str, Any], tflite: dict[str, Any]) -> None:
    metadata = read_json(MOBILE_METADATA)
    if metadata.get("model_version") != MODEL_VERSION:
        fail("Mobile metadata model version is not the shared contract version")
    if metadata.get("class_order") != CLASSES:
        fail(
            f"Mobile metadata class order is {metadata.get('class_order')}; expected {CLASSES}"
        )
    if metadata.get("class_indices") != {
        str(i): label for i, label in enumerate(CLASSES)
    }:
        fail("Mobile metadata class_indices does not match class_order")
    if metadata.get("asset") != MOBILE_MODEL.name:
        fail("Mobile metadata asset does not name jenis_fp32.tflite")
    if (
        metadata.get("sha256") != tflite["sha256"]
        or metadata.get("size_bytes") != tflite["size_bytes"]
    ):
        fail("Mobile metadata checksum or size does not match jenis_fp32.tflite")

    tensor_contract = metadata.get("tensor_contract", {})
    if (
        tensor_contract.get("input_shape") != INPUT_SHAPE
        or tensor_contract.get("output_shape") != OUTPUT_SHAPE
    ):
        fail("Mobile metadata tensor shapes do not match the TFLite artifact")
    if (
        tensor_contract.get("input_dtype") != INPUT_DTYPE
        or tensor_contract.get("output_dtype") != OUTPUT_DTYPE
    ):
        fail("Mobile metadata tensor dtypes do not match the TFLite artifact")
    if (
        tensor_contract.get("input_tensor_count") != 1
        or tensor_contract.get("output_tensor_count") != 1
    ):
        fail("Mobile metadata tensor counts must both be one")

    backend_metadata = metadata.get("backend_artifact", {})
    if backend_metadata.get("path") != "apps/backend/model/best.keras":
        fail("Mobile metadata backend artifact path is incorrect")
    if (
        backend_metadata.get("sha256") != keras["sha256"]
        or backend_metadata.get("size_bytes") != keras["size_bytes"]
    ):
        fail("Mobile metadata backend checksum or size does not match best.keras")

    preprocessing = metadata.get("preprocessing", {})
    if (
        preprocessing.get("input_size") != [224, 224]
        or preprocessing.get("channels") != 3
    ):
        fail("Mobile preprocessing metadata does not describe 224x224 RGB input")
    if (
        preprocessing.get("color_mode") != "RGB"
        or preprocessing.get("input_dtype") != INPUT_DTYPE
    ):
        fail("Mobile preprocessing metadata must describe RGB float32 input")
    if (
        preprocessing.get("input_range") != [0, 255]
        or preprocessing.get("rescale") != "none"
    ):
        fail("Mobile preprocessing metadata must describe raw [0, 255] input")
    internal = preprocessing.get("model_internal_rescaling", {})
    if not isinstance(internal, dict):
        fail("Mobile metadata internal rescaling is missing")
    require_float(
        internal.get("scale"),
        RESCALING_SCALE,
        "Mobile metadata internal rescaling scale",
    )
    require_float(
        internal.get("offset"),
        RESCALING_OFFSET,
        "Mobile metadata internal rescaling offset",
    )
    print(f"PASS metadata: version={MODEL_VERSION}, class order and checksums match")


def validate_source_defaults() -> None:
    checks = [
        (
            "apps/backend/config.py",
            r'MODEL_CONTRACT_CLASSES\s*:[^=]+\s*=\s*\([\s\S]*?"bali",\s*"brahman",\s*"brangus",\s*"limusin",\s*\)',
        ),
        (
            "apps/backend/config.py",
            r'model_path:\s*str\s*=\s*os\.getenv\("MODEL_PATH",\s*"\./model/best\.keras"\)',
        ),
        (
            "apps/backend/model/loader.py",
            r'def __new__\(cls, model_path: str = "\./model/best\.keras"\)',
        ),
        (
            "apps/backend/docker-compose.yml",
            r"MODEL_PATH=\$\{MODEL_PATH:-\./model/best\.keras\}",
        ),
        ("apps/backend/.env.example", r"MODEL_PATH=\./model/best\.keras"),
        ("apps/mobile/app/build.gradle.kts", r"MODEL_FILE_NAME.*jenis_fp32\.tflite"),
        (
            "apps/mobile/app/build.gradle.kts",
            rf"MODEL_VERSION.*{MODEL_VERSION}",
        ),
        ("apps/mobile/local.properties.example", r"MODEL_FILE_NAME=jenis_fp32\.tflite"),
        (
            "apps/mobile/local.properties.example",
            rf"MODEL_VERSION={MODEL_VERSION}",
        ),
        (
            "apps/mobile/app/src/main/java/id/sapikenal/app/ml/OfflineInferenceEngine.kt",
            r'listOf\("bali",\s*"brahman",\s*"brangus",\s*"limusin"\)',
        ),
    ]
    for relative, pattern in checks:
        path = ROOT / relative
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            fail(f"Cannot read {relative}: {exc}")
        if not re.search(pattern, content):
            fail(f"Contract default missing from {relative}")
    print("PASS backend/mobile defaults use the shared model artifacts and class order")


def validate_backend_environment() -> None:
    """Verify the documented backend environment resolves the breed contract."""
    env_path = ROOT / "apps/backend/.env.example"
    values: dict[str, str] = {}
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            values[name] = value
    except OSError as exc:
        fail(f"Cannot read apps/backend/.env.example: {exc}")

    if values.get("MODEL_PATH") != "./model/best.keras":
        fail(".env.example MODEL_PATH must point to ./model/best.keras")
    if values.get("MODEL_VERSION") != MODEL_VERSION:
        fail(".env.example MODEL_VERSION must match the shared contract version")

    class_names_value = values.get("MODEL_CLASS_NAMES_PATH")
    if not class_names_value:
        fail(".env.example must define MODEL_CLASS_NAMES_PATH")
    class_names_path = (env_path.parent / class_names_value).resolve()
    if class_names_path != BACKEND_CLASSES.resolve():
        fail(
            ".env.example class names path must point to backend/model/class_names.json"
        )
    class_names = read_json(class_names_path)
    if not isinstance(class_names, dict):
        fail("The effective .env.example class names file must be a JSON object")
    if [class_names.get(str(index)) for index in range(len(CLASSES))] != CLASSES:
        fail("The effective .env.example class names file has the wrong class order")

    config_path = ROOT / "apps/backend/config.py"
    try:
        config_text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Cannot read apps/backend/config.py: {exc}")
    if 'raw_path = os.getenv("MODEL_CLASS_NAMES_PATH")' not in config_text:
        fail("Backend config does not load the documented class names setting")
    if "if labels != list(CANONICAL_LABELS):" not in config_text:
        fail("Backend config does not validate class names against the active contract")
    print("PASS effective backend environment matches the active class contract")


def validate_backend_consumer() -> None:
    config_path = ROOT / "apps/backend/config.py"
    inference_path = ROOT / "apps/backend/inference_server.py"

    try:
        config_text = config_path.read_text(encoding="utf-8")
        inference_text = inference_path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Cannot read backend source files for consumer check: {exc}")

    canonical_match = re.search(
        r"CANONICAL_LABELS\s*(?::[^=]+)?\s*=\s*([^\n]+)",
        config_text,
        re.DOTALL,
    )
    if not canonical_match:
        fail("Cannot find CANONICAL_LABELS definition in apps/backend/config.py")
    active_labels = [
        s.strip().strip('"').strip("'")
        for s in canonical_match.group(1).split(",")
        if s.strip().strip('"').strip("'")
    ]

    map_match = re.search(r"DISPLAY_LABEL_KEY_MAP\s*=\s*\{([^}]+)\}", inference_text)
    if map_match:
        map_keys = re.findall(r'["\']([^"\']+)["\']\s*:', map_match.group(1))
        missing = [label for label in active_labels if label not in map_keys]
        if missing:
            fail(
                f"Backend runtime consumer in inference_server.py is missing display key mappings for active labels: {missing}. "
                "Active runtime CANONICAL_LABELS and DISPLAY_LABEL_KEY_MAP must remain compatible."
            )

    print("PASS backend consumer and active runtime labels are mutually compatible")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="exercise valid and malformed TFLite graph contract checks",
    )
    args = parser.parse_args()
    try:
        if args.self_test:
            run_self_check()
            return 0
        validate_class_names()
        keras_metadata = validate_keras()
        tflite_metadata = validate_tflite()
        validate_source_defaults()
        validate_backend_environment()
        validate_backend_consumer()
        validate_metadata(keras_metadata, tflite_metadata)
    except (
        ContractError,
        KeyError,
        TypeError,
        ValueError,
        OSError,
        struct.error,
    ) as exc:
        print("MODEL CONTRACT FAILED", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 1
    print("MODEL CONTRACT OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
