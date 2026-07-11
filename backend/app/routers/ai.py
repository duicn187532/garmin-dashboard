from fastapi import APIRouter, Depends

from ..schemas import AiAnalyzeRequest, AiQueryRequest, AiReportResponse
from ..store import MongoDataStore, SqlDataStore, get_store


router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/analyze", response_model=AiReportResponse)
def analyze(
    request: AiAnalyzeRequest,
    store: SqlDataStore | MongoDataStore = Depends(get_store),
):
    return store.analyze_today()


@router.post("/query", response_model=AiReportResponse)
def query(
    request: AiQueryRequest,
    store: SqlDataStore | MongoDataStore = Depends(get_store),
):
    return store.answer_question(request.question)


@router.get("/latest", response_model=AiReportResponse | None)
def latest_report(store: SqlDataStore | MongoDataStore = Depends(get_store)):
    return store.latest_ai()


@router.get("/reports", response_model=list[AiReportResponse])
def reports(store: SqlDataStore | MongoDataStore = Depends(get_store)):
    return store.ai_reports()

