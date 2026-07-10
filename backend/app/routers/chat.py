from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse
from app.services import chat_service

router = APIRouter(prefix="/api/dataset", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    answer, chunks = chat_service.answer_question(
        request.dataset_id, request.question, top_k=request.top_k
    )
    return ChatResponse(answer=answer, used_chunks=chunks)
