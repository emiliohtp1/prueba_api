from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
from pymongo import MongoClient
from typing import List, Optional, Literal
import os
from models import ProductoRopa
from azure.storage.blob import BlobServiceClient

# Leer la URI desde variables de entorno
MONGO_URI = os.getenv("MONGO_URI")
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_BLOB_CONTAINER_NAME = os.getenv("AZURE_BLOB_CONTAINER_NAME", "imagenes-productos")

if not MONGO_URI:
    raise ValueError("MONGO_URI no está definida")

if not AZURE_STORAGE_CONNECTION_STRING:
    raise ValueError("AZURE_STORAGE_CONNECTION_STRING no está definida")

print(f"Conectando a MongoDB en: {MONGO_URI}")
print(f"Conectando a Azure Blob Storage en: {AZURE_BLOB_CONTAINER_NAME}")

client = MongoClient(MONGO_URI)
db = client["prueba"]
collection = db["prueba_collection"]

# Inicializar cliente de Azure Blob Storage
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_BLOB_CONTAINER_NAME)

app = FastAPI()

class ProductosInput(BaseModel):
    productos: List[ProductoRopa]

@app.post("/productos")
async def create_productos(
    product_type: Literal["pant", "shirt", "tshirt", "cap", "belt"] = Form(...),
    size: Literal["XS", "S", "M", "G", "XG"] = Form(...),
    price: float = Form(...),
    amount: int = Form(...),
    image: Optional[UploadFile] = File(None)
):
    image_url = None
    if image:
        # Subir imagen a Azure Blob Storage
        file_name = f"{image.filename}"
        blob_client = container_client.get_blob_client(file_name)
        blob_client.upload_blob(await image.read(), overwrite=True)
        image_url = blob_client.url

    producto_data = {
        "product_type": product_type,
        "size": size,
        "price": price,
        "amount": amount,
        "image_url": image_url
    }
    
    result = collection.insert_one(producto_data)

    return {
        "inserted_id": str(result.inserted_id),
        "msg": "Producto agregado correctamente"
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