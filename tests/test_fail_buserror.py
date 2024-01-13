import uuid
from datetime import datetime, timezone
from typing import Any, Type
from uuid import UUID

import pytest
import pytest_asyncio
import sqlalchemy as sa
from pydantic_core import CoreSchema, core_schema
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import (
    _AsyncSessionContextManager as AsyncSessionContextManager,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column, registry
from sqlalchemy.types import DateTime

from pydantic import GetCoreSchemaHandler
from pydantic.main import BaseModel


class UTCTime(datetime):
    @staticmethod
    def _perform_validation(value: datetime, strict: bool = True):
        if value.tzinfo is None:
            if strict:
                raise ValueError('Timezone Info should be passed')
            # Assume it's in UTC
            return value.astimezone(timezone.utc)

        elif value.tzinfo != timezone.utc:
            # Convert to UTC if it's not
            return value.astimezone(timezone.utc)
        else:
            # It's already in UTC
            return value

    def __new__(cls, value: datetime, strict: bool = True, *args, **kwargs):
        if isinstance(value, datetime):
            value = cls._perform_validation(value, strict)
            return super().__new__(
                cls,
                value.year,
                value.month,
                value.day,
                value.hour,
                value.minute,
                value.second,
                value.microsecond,
                timezone.utc,
            )

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(datetime))


class UTCBiggerThanNow(UTCTime):
    @staticmethod
    def _perform_validation(value: datetime, strict: bool = True):
        value = UTCTime._perform_validation(value, strict)
        if value < datetime.now(timezone.utc):
            raise ValueError('UTC Datetime should be bigger than now')

        return value


SQLRegistry = registry(
    type_annotation_map={
        datetime: DateTime(timezone=True),
    }
)


class SQLBase(MappedAsDataclass, DeclarativeBase):
    registry = SQLRegistry


class MarketRelation(SQLBase):
    __tablename__ = 'MarketRelation'

    buyer_id: Mapped[UUID] = mapped_column()
    seller_id: Mapped[UUID] = mapped_column()
    expires_at: Mapped[datetime] = mapped_column()
    # TODO: what about relation that can be extended? maybe allowing null value here?

    max_debt: Mapped[int] = mapped_column()
    current_debt: Mapped[int] = mapped_column()

    local_price: Mapped[int] = mapped_column(default=100)
    global_is_allowed_to_order: Mapped[bool] = mapped_column(default=True)
    is_allow_to_order: Mapped[bool] = mapped_column(default=True)

    remover_id: Mapped[UUID | None] = mapped_column(default=None)
    """Threesholder for the person who removed the Relation"""
    # TODO: should this be timeseries?

    is_accepted: Mapped[bool] = mapped_column(default=False)

    is_waiting: Mapped[bool] = mapped_column(default=True)
    """Threesholder for a relation that hasn't bee approved/rejected yet"""

    is_banned: Mapped[bool] = mapped_column(default=False)

    id: Mapped[UUID] = mapped_column(primary_key=True, default_factory=uuid.uuid4)
    created_at: Mapped[datetime | None] = mapped_column(default_factory=lambda: datetime.now(timezone.utc))


class DatabaseManager:
    def __init__(self, model_base: Type[DeclarativeBase], db_url: str | URL, **kwargs) -> None:
        self.model_base = model_base

        if not isinstance(db_url, URL):
            db_url = sa.make_url(db_url)

        self.db_url = db_url
        self.engine = create_async_engine(
            db_url,
            **kwargs,
        )
        self.sessionmaker = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
            autobegin=False,
        )

    async def drop_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(self.model_base.metadata.drop_all)

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(self.model_base.metadata.create_all)

    def begin(self) -> AsyncSessionContextManager[AsyncSession]:
        """Returns a AsyncSession with a transaction started. Commits and closes"""
        return self.sessionmaker.begin()


async def create(
    db_session: DatabaseManager,
    seller_id: UUID,
    buyer_id: UUID,
    expires_at: datetime,
    max_debt: int,
    is_allow_to_order: bool,
    global_is_allowed_to_order: bool,
    local_price: int,
):
    async with db_session.begin() as session:
        obj = MarketRelation(
            buyer_id=buyer_id,
            seller_id=seller_id,
            expires_at=expires_at,
            max_debt=max_debt,
            current_debt=0,
            is_allow_to_order=is_allow_to_order,
            global_is_allowed_to_order=global_is_allowed_to_order,
            local_price=local_price,
        )
        session.add(obj)

    return obj


class CreateBuySellRelationInput(BaseModel):
    buyer_id: UUID
    seller_id: UUID
    expires_at: UTCBiggerThanNow
    max_debt: int
    is_allow_to_order: bool = True
    global_is_allowed_to_order: bool = True
    local_price: int = 100


@pytest_asyncio.fixture
async def get_db():
    db_string_url = 'postgresql+asyncpg://admin:admin@localhost:5440/marketplace'
    db_manager = DatabaseManager(model_base=SQLBase, db_url=db_string_url)
    await db_manager.drop_tables()
    await db_manager.create_tables()
    yield db_manager
    await db_manager.drop_tables()


@pytest.mark.asyncio
async def test_bus_error(get_db: DatabaseManager):
    seller = '463d946d-8bb9-4dac-b0f0-13783d6dca92'
    buyer = 'a6ae6e74-6589-48cd-9618-41383a35abd4'

    json_input = {
        'buyer_id': buyer,
        'seller_id': seller,
        'expires_at': '2050-12-20T12:37:34.607Z',
        'max_debt': 0,
        'is_allow_to_order': True,
        'global_is_allowed_to_order': True,
        'local_price': 100,
    }
    data = CreateBuySellRelationInput(**json_input)

    await create(
        db_session=get_db,
        buyer_id=data.buyer_id,
        seller_id=data.seller_id,
        expires_at=data.expires_at,
        max_debt=data.max_debt,
        is_allow_to_order=data.is_allow_to_order,
        global_is_allowed_to_order=data.global_is_allowed_to_order,
        local_price=data.local_price,
    )
