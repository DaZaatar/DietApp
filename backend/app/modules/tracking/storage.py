from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


class LocalMediaStorage:
    def __init__(self, root: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload: UploadFile, prefix: str = "tracking") -> tuple[str, int]:
        ext = Path(upload.filename or "file.bin").suffix
        storage_key = f"{prefix}/{uuid4().hex}{ext}"
        file_path = self.root / storage_key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        content = await upload.read()
        file_path.write_bytes(content)
        return storage_key, len(content)

    def delete_file(self, storage_key: str) -> None:
        path = self.root / storage_key
        if path.is_file():
            path.unlink()
