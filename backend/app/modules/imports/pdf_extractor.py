from io import BytesIO

from fastapi import HTTPException, UploadFile
from pypdf import PdfReader


class PDFExtractor:
    async def extract_text(self, upload: UploadFile) -> str:
        if upload.content_type not in {"application/pdf", "application/octet-stream"}:
            raise HTTPException(status_code=400, detail="Expected PDF file")

        content = await upload.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty PDF")

        try:
            reader = PdfReader(BytesIO(content))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages).strip()
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"PDF parsing failed: {exc}") from exc
