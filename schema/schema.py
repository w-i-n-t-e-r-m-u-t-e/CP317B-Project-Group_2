from typing import Annotated
from fastapi import Body, FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

# Define your data schema using Pydantic models
class Product(BaseModel):
    # Required field with minimum length validation
    name: str = Field(min_length=2, max_length=50, description="The unique name of the product")
    
    # Optional field with a default value and structural validation
    description: str | None = Field(default=None, max_length=300, title="Product Description")
    
    # Numeric validation (must be greater than 0)
    price: float = Field(gt=0, description="The price must be a positive number")
    
    # Optional field with a default factory to handle mutable types safely
    tags: list[str] = Field(default_factory=list, description="Associated search keywords")

@app.post("/products/")
async def create_product(product: Product):
    return {"message": "Product created successfully", "data": product}