from __future__ import annotations

import os
import tempfile
from pathlib import Path

_history_tmp = tempfile.TemporaryDirectory(prefix="sapikenal-pytest-")
os.environ["HISTORY_DB_PATH"] = str(Path(_history_tmp.name) / "history.sqlite3")
