from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from typing import List

# Tu URI completo de MongoDB Atlas
MONGO_URI = "mongodb+srv://emiliohtp_db_user:PUyvTLcwWKOQ4wwM@cluster0.cvdcchr.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["prueba"]
collection = db["prueba_collection"]

app = FastAPI()

class ProductosInput(BaseModel):
    productos: List[str]

@app.post("/productos")
def create_productos(data: ProductosInput):
    docs = [{"nombre": producto} for producto in data.productos]
    result = collection.insert_many(docs)
    return {"inserted_ids": [str(_id) for _id in result.inserted_ids], "msg": "Productos agregados correctamente"}

@app.get("/productos")
def get_productos():
    productos = [{"id": str(doc["_id"]), "nombre": doc["nombre"]} for doc in collection.find()]
    return productos
