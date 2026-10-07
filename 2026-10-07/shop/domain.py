"""Domain models and validation rules."""

from pydantic import BaseModel, ConfigDict, Field


class Product(BaseModel):
    """A product displayed in the catalog."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    price: int = Field(ge=0)
