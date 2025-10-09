from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Schema genérico para respuestas paginadas"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Schema para respuestas de error"""
    detail: str
    error_code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Schema para respuestas exitosas"""
    message: str
    data: Optional[dict] = None