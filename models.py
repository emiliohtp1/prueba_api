from pydantic import BaseModel
from typing import Literal

class ProductoRopa(BaseModel):
    product_type: Literal["pant", "shirt", "tshirt", "cap", "belt"]
    size: Literal["XS", "S", "M", "G", "XG"]
    price: float
    amount: int
