#!/usr/bin/env python3
"""Capture real local fixtures on one explicitly selected Android device.

Requires the current debug app and androidTest APKs to be installed. Does not
install apps, change server state, or add any images/tensors to Git.
"""

import argparse
import hashlib
import json
import subprocess
import uuid
from pathlib import Path

CLASSES = ("bali", "brahman", "brangus", "limusin")
APP = "id.sapikenal.app"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixtures = []
    for label in CLASSES:
        images = sorted((args.fixtures / label).glob("*.jpg"))
        if not images or any(not p.is_file() or p.is_symlink() for p in images):
            parser.error(f"Expected real, regular JPEG fixtures in {label}/")
        fixtures.extend(images)
    args.output.mkdir(parents=True, exist_ok=False)
    run_id = "parity-" + uuid.uuid4().hex
    adb = ["adb", "-s", args.serial]

    def run(*command, data=None):
        return subprocess.run(
            [*adb, *command],
            input=data,
            capture_output=True,
            check=True,
            timeout=240,
        ).stdout

    run("shell", "run-as", APP, "mkdir", "-p", f"files/{run_id}/input")
    try:
        manifest = []
        for index, fixture in enumerate(fixtures, 1):
            source_name = f"fixture-{index:03d}.jpg"
            output_name = f"fixture-{index:03d}.png"
            data = fixture.read_bytes()
            run(
                "shell",
                "-T",
                "run-as",
                APP,
                "sh",
                "-c",
                f"'cat > files/{run_id}/input/{source_name}'",
                data=data,
            )
            staged = run(
                "exec-out", "run-as", APP, "cat", f"files/{run_id}/input/{source_name}"
            )
            if staged != data:
                raise RuntimeError(
                    f"Android fixture transfer did not preserve bytes: {source_name}"
                )
            manifest.append(
                {
                    "id": output_name,
                    "path": str(fixture.relative_to(args.fixtures)),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
        log = run(
            "shell",
            "am",
            "instrument",
            "-w",
            "-r",
            "-e",
            "parityRun",
            run_id,
            "-e",
            "class",
            "id.sapikenal.app.ml.ModelParityCaptureTest",
            f"{APP}.test/androidx.test.runner.AndroidJUnitRunner",
        ).decode()
        (args.output / "instrumentation.txt").write_text(log)
        if "OK (1 test)" not in log:
            raise RuntimeError(
                f"Android capture failed; see {args.output}/instrumentation.txt\n{log}"
            )
        for name in [
            "android.json",
            *[suffix for row in manifest for suffix in (row["id"], row["id"] + ".f32")],
        ]:
            (args.output / name).write_bytes(
                run("exec-out", "run-as", APP, "cat", f"files/{run_id}/output/{name}")
            )
        (args.output / "fixtures.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )
    finally:
        run("shell", "run-as", APP, "rm", "-rf", f"files/{run_id}")
    print(
        f"Captured {len(fixtures)} real fixtures in {args.output}; parity NOT yet evaluated"
    )


if __name__ == "__main__":
    main()
