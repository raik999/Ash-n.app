from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from config.database import get_db
from controllers import tag_controller
from middleware.auth_middleware import require_admin
from validations.user_validation import TagResponse

router = APIRouter(prefix="/api/tags", tags=["Especialidades"])


class CreateTagRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=40)
    color: str = Field(default="#7C7C7C", pattern=r"^#[0-9A-Fa-f]{6}$")


@router.get(
    "",
    response_model=list[TagResponse],
    summary="Listar todas las especialidades",
)
def list_tags(db: Session = Depends(get_db)) -> list[TagResponse]:
    return tag_controller.list_tags(db)


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
    summary="Crear una especialidad (solo admin)",
)
def create_tag(
    payload: CreateTagRequest,
    db: Session = Depends(get_db),
) -> TagResponse:
    return tag_controller.create_tag(db, name=payload.name, color=payload.color)
