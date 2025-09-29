from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from typing import List
import os
from models import ProductoRopa

# Leer la URI desde variables de entorno
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI no está definida")

print(f"Conectando a MongoDB en: {MONGO_URI}")

client = MongoClient(MONGO_URI)
db = client["prueba"]
collection = db["prueba_collection"]

app = FastAPI()

class ProductosInput(BaseModel):
    productos: List[ProductoRopa]

@app.post("/productos")
def create_productos(data: ProductosInput):
    docs = [producto.dict() for producto in data.productos]
    result = collection.insert_many(docs)
    return {
        "inserted_ids": [str(_id) for _id in result.inserted_ids],
        "msg": "Productos agregados correctamente"
    }

@app.get("/get_productos")
def get_productos():
    productos = []
    for doc in collection.find():
        producto = {
            "id": str(doc["_id"]),
            "product_type": doc.get("product_type"),
            "size": doc.get("size"),
            "price": doc.get("price"),
            "amount": doc.get("amount")
        }
        productos.append(producto)
    return productos