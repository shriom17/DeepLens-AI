import uuid

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from backend.services.notice_processor import process_notice, process_notice_url


router = APIRouter()

# NOTE: This is an in-memory store, mirroring the simple demo behavior in
# app.py. It will reset on restart and isn't safe for multi-worker deployments.
NOTICES: dict[str, dict] = {}


def _store_result(notice_data: dict, source_label: str) -> str:
    doc_id = str(uuid.uuid4())
    NOTICES[doc_id] = {
        "data": notice_data,
        "filename": source_label,
    }
    return doc_id


class AnalyzeUrlPayload(BaseModel):
    url: str


@router.post("/analyze")
async def analyze_content(
    url: str = Form(None),
    file: UploadFile = File(None)
):
    try:
        if file:
            pdf_bytes = await file.read()

            print("FILE:", file.filename)
            print("CONTENT TYPE:", file.content_type)
            print("FILE SIZE:", len(pdf_bytes))
            print("FIRST BYTES:", pdf_bytes[:20])
            print("MAGIC:", pdf_bytes[:4])

            if not pdf_bytes:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded PDF is empty"
                )

            notice_data = process_notice(pdf_bytes)
            doc_id = _store_result(notice_data, file.filename or "uploaded")
            return {"id": doc_id, "data": notice_data}

        if url:
            notice_data = process_notice_url(url)
            doc_id = _store_result(notice_data, url)
            return {"id": doc_id, "data": notice_data}

        raise HTTPException(
            status_code=400,
            detail="Please provide a URL or PDF file"
        )

    except HTTPException:
        raise

    except Exception as e:
        print("ANALYZE ERROR:", repr(e))
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/analyze-url")
async def analyze_url(payload: AnalyzeUrlPayload):
    try:
        url = (payload.url or "").strip()
        if not url:
            raise HTTPException(status_code=400, detail="No URL provided")

        notice_data = process_notice_url(url)
        doc_id = _store_result(notice_data, url)
        return {"id": doc_id, "data": notice_data}
    except HTTPException:
        raise
    except Exception as e:
        print("ANALYZE-URL ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notices")
def list_notices():
    # Return the same shape app.py expects.
    result = [
        {"id": nid, "data": n.get("data"), "filename": n.get("filename")}
        for nid, n in NOTICES.items()
    ]
    # Latest-first isn't meaningful without created_at; keep deterministic ordering.
    return sorted(result, key=lambda item: item["id"], reverse=True)