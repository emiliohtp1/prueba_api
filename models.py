from pydantic import BaseModel
from typing import Literal, Optional, Dict

class ProductoRopa(BaseModel):
    product_type: Literal["pant", "shirt", "tshirt", "cap", "belt"]
    product_name: str
    size: Literal["XS", "S", "M", "L", "XL", "XXL"]
    price: float
    amount: int
    image_url: Optional[str] = None


class ProductoDetalle(BaseModel):
    id: str
    product_type: Literal["pant", "shirt", "tshirt", "cap", "belt"]
    size: Literal["XS", "S", "M", "L", "XL", "XXL"]
    price: float
    amount: int
    image_url: Optional[str] = None


class ProductosRespuesta(BaseModel):
    products: Dict[str, Dict[str, Dict[str, ProductoDetalle]]]
