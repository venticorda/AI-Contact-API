from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.response import ContactListItem, ContactListResponse
from app.database.models import Contact
from app.database.session import async_session_factory

router = APIRouter(prefix="/api", tags=["Contacts"])


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


@router.get(
    "/contacts",
    response_model=ContactListResponse,
    summary="Получить список контактов",
    description="Возвращает список контактных форм с пагинацией.",
)
async def list_contacts(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> ContactListResponse:
    offset = (page - 1) * per_page

    total_result = await db.execute(select(func.count(Contact.id)))
    total = total_result.scalar() or 0

    result = await db.execute(
        select(Contact).order_by(Contact.created_at.desc()).offset(offset).limit(per_page)
    )
    contacts = result.scalars().all()

    items = [
        ContactListItem(
            id=c.id,
            name=c.name,
            email=c.email,
            phone=c.phone,
            sentiment=c.sentiment,
            created_at=c.created_at.isoformat() if c.created_at else None,
        )
        for c in contacts
    ]

    return ContactListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page if total else 0,
    )
