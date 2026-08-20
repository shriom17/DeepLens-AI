from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from backend.services.paper_analyzer import analyze


router = APIRouter()


@router.post("/analyze")
async def analyze_content(
    url: str = Form(None),
    file: UploadFile = File(None)
):
    try:

        if file:
            pdf_bytes = await file.read()

            result = analyze(
                pdf_bytes,
                file.filename
            )

            return result.model_dump()

        if url:
            result = analyze(url)

            return result.model_dump()

        raise HTTPException(
            status_code=400,
            detail="Please provide a URL or PDF file"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )