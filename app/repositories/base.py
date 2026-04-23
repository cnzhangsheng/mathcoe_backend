"""
Generic repository base class with CRUD operations
"""
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Generic repository with basic CRUD operations"""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, data: dict[str, Any]) -> ModelType:
        """Create a new record"""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, id: int) -> ModelType | None:
        """Get a record by ID"""
        result = await self.session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[ModelType]:
        """Get all records with pagination"""
        result = await self.session.execute(select(self.model).limit(limit).offset(offset))
        return list(result.scalars().all())

    async def update(self, id: int, data: dict[str, Any]) -> ModelType | None:
        """Update a record by ID"""
        instance = await self.get_by_id(id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        """Delete a record by ID"""
        instance = await self.get_by_id(id)
        if instance is None:
            return False
        await self.session.delete(instance)
        await self.session.commit()
        return True

    async def exists(self, id: int) -> bool:
        """Check if a record exists"""
        result = await self.session.execute(select(self.model.id).where(self.model.id == id))
        return result.scalar_one_or_none() is not None