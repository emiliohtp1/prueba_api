from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

db_password = "PUyvTLcwWKOQ4wwM"
mongo_link = f"mongodb+srv://emiliohtp_db_user:{db_password}@cluster0.cvdcchr.mongodb.net/"

# Conexión a MongoDB (desde variable de entorno)
MONGO_URI = os.getenv("mongo_link")
client = MongoClient(MONGO_URI)
db = client["prueba"]   # base de datos
collection = db["prueba_collection"]

# App FastAPI
app = FastAPI()

# Modelo para la entrada de datos
class Item(BaseModel):
    name: str
    description: str

@app.get("/")
def root():
    return {"msg": "API FastAPI + MongoDB funcionando en Render"}

@app.post("/items")
def create_item(item: Item):
    result = collection.insert_one(item.dict())
    return {"id": str(result.inserted_id), "msg": "Item creado"}

@app.get("/items")
def get_items():
    items = []
    for doc in collection.find():
        items.append({
            "id": str(doc["_id"]),
            "name": doc["name"],
            "description": doc["description"]
        })
    return items
