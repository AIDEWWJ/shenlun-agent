from typing import Literal

from pydantic import BaseModel, Field


LibraryItemType = Literal["paper", "question"]
LibraryItemTypeFilter = Literal["all", "paper", "question"]


class LibraryAction(BaseModel):
    label: str
    path: str


class LibraryItemRead(BaseModel):
    item_key: str
    item_type: LibraryItemType
    resource_id: int
    title: str
    source: str | None = None
    year: int | None = None
    region: str | None = None
    difficulty: str | None = None
    question_type: str | None = None
    question_count: int | None = None
    suggested_minutes: int | None = None
    scope: str
    tags: list[str] = Field(default_factory=list)
    has_draft: bool = False
    created_at: str | None = None
    updated_at: str | None = None
    primary_action: LibraryAction
    secondary_action: LibraryAction | None = None


class LibraryItemListResponse(BaseModel):
    items: list[LibraryItemRead] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    applied_filters: dict[str, str | int | None] = Field(default_factory=dict)
    applied_sort: dict[str, str] = Field(default_factory=dict)


class LibraryFilterOptionsResponse(BaseModel):
    item_types: list[LibraryItemType] = Field(default_factory=lambda: ["paper", "question"])
    scopes: list[str] = Field(default_factory=lambda: ["system", "user"])
    regions: list[str] = Field(default_factory=list)
    years: list[int] = Field(default_factory=list)
    difficulties: list[str] = Field(default_factory=list)
    question_types: list[str] = Field(default_factory=list)
    sort_fields: list[Literal["created_at", "updated_at", "year", "title"]] = Field(
        default_factory=lambda: ["created_at", "updated_at", "year", "title"],
    )
    default_sort_by: Literal["created_at"] = "created_at"
    default_sort_order: Literal["desc"] = "desc"

