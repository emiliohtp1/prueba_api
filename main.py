from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
from pymongo import MongoClient
from typing import List, Optional, Literal
import os
from models import ProductoRopa
from azure.storage.blob import BlobServiceClient
from token_blob_azure import build_blob_sas_url
from azure.storage.blob import ContentSettings
from io import BytesIO
from PIL import Image

# Leer la URI desde variables de entorno
MONGO_URI = os.getenv("MONGO_URI")
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_BLOB_CONTAINER_NAME = os.getenv("AZURE_BLOB_CONTAINER_NAME", "imagenes-productos")
AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

if not MONGO_URI:
    raise ValueError("MONGO_URI no está definida")

if not AZURE_STORAGE_CONNECTION_STRING:
    raise ValueError("AZURE_STORAGE_CONNECTION_STRING no está definida")

if not AZURE_STORAGE_ACCOUNT_NAME:
    raise ValueError("AZURE_STORAGE_ACCOUNT_NAME no está definida")

if not AZURE_STORAGE_ACCOUNT_KEY:
    raise ValueError("AZURE_STORAGE_ACCOUNT_KEY no está definida")

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
        # Leer bytes originales
        original_bytes = await image.read()

        # Abrir con Pillow, redimensionar y comprimir
        with Image.open(BytesIO(original_bytes)) as im:
            # Convertir a modo adecuado y preservar orientación EXIF
            try:
                im = Image.open(BytesIO(original_bytes))
            except Exception:
                pass
            # Limitar tamaño máximo (ej. 1280px lado mayor)
            max_size = (400, 400)
            im.thumbnail(max_size, Image.LANCZOS)

            # Elegir formato de salida y content-type
            format_out = "JPEG"
            content_type_out = "image/jpeg"
            if im.mode in ("RGBA", "LA"):
                # Si hay transparencia, usa PNG para evitar fondo negro
                format_out = "PNG"
                content_type_out = "image/png"
                if im.mode not in ("RGBA", "LA"):
                    im = im.convert("RGBA")
            else:
                if im.mode != "RGB":
                    im = im.convert("RGB")

            out_buffer = BytesIO()
            if format_out == "JPEG":
                im.save(out_buffer, format=format_out, quality=80, optimize=True, progressive=True)
            else:
                im.save(out_buffer, format=format_out, optimize=True)
            out_buffer.seek(0)

        # Preparar nombre de archivo con extensión acorde al formato de salida
        base_name = os.path.splitext(image.filename)[0] or "imagen"
        ext = ".jpg" if format_out == "JPEG" else ".png"
        file_name = f"{base_name}{ext}"

        # Subir imagen a Azure Blob Storage con tipo de contenido correcto
        blob_client = container_client.get_blob_client(file_name)
        content_settings = ContentSettings(
            content_type=content_type_out,
            content_disposition=f"inline; filename={file_name}"
        )
        blob_client.upload_blob(out_buffer.getvalue(), overwrite=True, content_settings=content_settings)

        # Generar URL SAS temporal (p. ej. 60 minutos)
        image_url = build_blob_sas_url(
            account_name=AZURE_STORAGE_ACCOUNT_NAME,
            account_key=AZURE_STORAGE_ACCOUNT_KEY,
            container_name=AZURE_BLOB_CONTAINER_NAME,
            blob_name=file_name,
            expiry_minutes=60,
            https_only=True,
        )

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