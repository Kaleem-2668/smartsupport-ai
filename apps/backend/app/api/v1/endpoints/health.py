from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Liveness probe — intentionally has no dependencies.
    A /health/ready endpoint checking DB/vector store lands in a later feature.
    """
    return {"status": "ok"}
