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
db = client[database]   # base de datos
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

@app.post("/items")
def create_item(item: Item):
    result = collection.insert_one(item.dict())
    return {"id": str(result.inserted_id), "msg": "Item creado"}

@app.get("/items")
def get_items():
    items = [{"id": str(doc["_id"]), "name": doc["name"], "description": doc["description"]} 
             for doc in collection.find()]
    return items

@app.post("/productos")
def create_productos(data: ProductosInput):
    docs = [{"nombre": producto} for producto in data.productos]
    result = collection.insert_many(docs)
    return {"inserted_ids": [str(_id) for _id in result.inserted_ids], "msg": "Productos agregados correctamente"}

@app.get("/productos")
def get_productos():
    productos = [{"id": str(doc["_id"]), "nombre": doc["nombre"]} for doc in collection.find()]
    return productos
