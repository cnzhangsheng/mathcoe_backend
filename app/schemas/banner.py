"""
Banner schemas - Pydantic models for banner management
"""
from datetime import datetime

from pydantic import BaseModel, field_validator


class BannerBase(BaseModel):
    image_url: str = ""
    link_type: str = "content"
    link_value: str = ""
    title: str = ""
    position: str = "home"
    sort_order: int = 0
    is_active: bool = True

    @field_validator("link_type")
    @classmethod
    def validate_link_type(cls, v: str) -> str:
        if v not in ("content", "external"):
            raise ValueError("link_type must be content or external")
        return v

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: str) -> str:
        allowed = ("home", "discover", "topics")
        if v not in allowed:
            raise ValueError(f"position must be one of {allowed}")
        return v


class BannerCreate(BannerBase):
    pass


class BannerUpdate(BaseModel):
    image_url: str | None = None
    link_type: str | None = None
    link_value: str | None = None
    title: str | None = None
    position: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None

    @field_validator("link_type")
    @classmethod
    def validate_link_type(cls, v: str | None) -> str | None:
        if v is not None and v not in ("content", "external"):
            raise ValueError("link_type must be content or external")
        return v

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: str | None) -> str | None:
        if v is not None:
            allowed = ("home", "discover", "topics")
            if v not in allowed:
                raise ValueError(f"position must be one of {allowed}")
        return v


class BannerResponse(BannerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BannerPublic(BannerBase):
    """小程序端返回的 Banner（只返回启用的）"""
    id: int

    model_config = {"from_attributes": True}
