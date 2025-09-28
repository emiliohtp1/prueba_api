from pymongo import MongoClient
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

# Conexión directa a MongoDB Atlas
db_user = "emiliohtp_db_user"
db_password = "PUyvTLcwWKOQ4wwM"
cluster = "cluster0.cvdcchr.mongodb.net"
database = "prueba"

MONGO_URI = f"mongodb+srv://{db_user}:{db_password}@{cluster}/{database}?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client[database]
collection = db["prueba_collection"]

app = FastAPI()

# Modelos
class Item(BaseModel):
    name: str
    description: str

class ProductosInput(BaseModel):
    productos: List[str]

# Endpoints
@app.get("/")
def root():
    return {"msg": "API FastAPI + MongoDB funcionando en Render"}

@app.post("/productos")
def create_productos(data: ProductosInput):
    docs = [{"nombre": producto} for producto in data.productos]
    result = collection.insert_many(docs)
    return {"inserted_ids": [str(_id) for _id in result.inserted_ids], "msg": "Productos agregados correctamente"}
