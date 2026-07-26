from __future__ import annotations

import shutil
import uuid
from pathlib import Path


class LocalTemporaryDirectory:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.path = self.root / f"tmp-{uuid.uuid4().hex}"
        self.name = str(self.path)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path.mkdir(parents=True, exist_ok=False)

    def __enter__(self) -> str:
        return self.name

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        self.cleanup()

    def cleanup(self) -> None:
        shutil.rmtree(self.path, ignore_errors=True)