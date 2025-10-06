from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
from pymongo import MongoClient
from typing import List, Optional, Literal, Dict
import os
from models import ProductoRopa, ProductosRespuesta, ProductoDetalle, ProductoDetallePlano
from azure.storage.blob import BlobServiceClient
from token_blob_azure import build_blob_sas_url
from azure.storage.blob import ContentSettings
from io import BytesIO
from PIL import Image
from pymongo.errors import DuplicateKeyError
from uuid import uuid4
from urllib.parse import urlparse

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

print(f"Conectando a MongoDB por MONGO_URI")
print(f"Conectando a Azure Blob Storage en: {AZURE_BLOB_CONTAINER_NAME}")

client = MongoClient(MONGO_URI)
Db = client["prueba"]
collection = Db["prueba_collection"]

# Asegurar índice único por combinación (product_type, product_name, size)
collection.create_index(
    [("product_type", 1), ("product_name", 1), ("size", 1)],
    unique=True,
    name="uq_product_variant"
)

# Inicializar cliente de Azure Blob Storage
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_BLOB_CONTAINER_NAME)

app = FastAPI()

class ProductosInput(BaseModel):
    productos: List[ProductoRopa]

@app.post("/productos")
async def create_productos(
    product_type: Literal["pant", "shirt", "tshirt", "cap", "belt", "shoes"] = Form(...),
    product_name: str = Form(...),
    size: Literal["XS", "S", "M", "L", "XL", "XXL"] = Form(...),
    price: float = Form(...),
    amount: int = Form(...),
    image: Optional[UploadFile] = File(None)
):
    blob_name: Optional[str] = None
    if image:
        # Leer bytes originales
        original_bytes = await image.read()

        # Abrir con Pillow, redimensionar y comprimir
        with Image.open(BytesIO(original_bytes)) as im:
            try:
                im = Image.open(BytesIO(original_bytes))
            except Exception:
                pass
            max_size = (400, 400)
            im.thumbnail(max_size, Image.LANCZOS)

            format_out = "JPEG"
            content_type_out = "image/jpeg"
            if im.mode in ("RGBA", "LA"):
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

        # Nombre único
        ext = ".jpg" if format_out == "JPEG" else ".png"
        blob_name = f"{uuid4().hex}{ext}"

        # Subir imagen
        blob_client = container_client.get_blob_client(blob_name)
        content_settings = ContentSettings(
            content_type=content_type_out,
            content_disposition=f"inline; filename={blob_name}"
        )
        blob_client.upload_blob(out_buffer.getvalue(), overwrite=False, content_settings=content_settings)

    # Documento base (guardar blob_name; no guardar image_url)
    producto_data = {
        "product_type": product_type,
        "product_name": product_name,
        "size": size,
        "price": price,
        "amount": amount,
        "blob_name": blob_name
    }

    # Upsert por combinación única
    query = {"product_type": product_type, "product_name": product_name, "size": size}
    try:
        result = collection.update_one(query, {"$set": producto_data}, upsert=True)
    except DuplicateKeyError:
        result = collection.update_one(query, {"$set": producto_data}, upsert=False)

    operation = "inserted" if result.upserted_id else ("updated" if result.matched_count > 0 else "no-op")

    # Obtener el _id del documento afectado
    if result.upserted_id:
        doc_id = str(result.upserted_id)
    else:
        doc = collection.find_one(query, {"_id": 1})
        doc_id = str(doc["_id"]) if doc else None

    return {
        "id": doc_id,
        "operation": operation,
        "msg": "Producto agregado/actualizado correctamente"
    }


def _infer_blob_name_from_legacy_url(image_url: Optional[str]) -> Optional[str]:
    if not image_url:
        return None
    try:
        parsed = urlparse(image_url)
        # path: /<container>/<blob_name>
        parts = parsed.path.split("/")
        if len(parts) >= 3:
            # última parte contiene blob + quizá no hay query en path
            return parts[-1]
    except Exception:
        return None
    return None


def _build_sas_for_blob(blob_name: Optional[str]) -> Optional[str]:
    if not blob_name:
        return None
    return build_blob_sas_url(
        account_name=AZURE_STORAGE_ACCOUNT_NAME,
        account_key=AZURE_STORAGE_ACCOUNT_KEY,
        container_name=AZURE_BLOB_CONTAINER_NAME,
        blob_name=blob_name,
        expiry_minutes=1440,
        https_only=True,
    )

@app.get("/get_productos", response_model=List[ProductoDetallePlano])
def get_productos():
    items: List[ProductoDetallePlano] = []
    for doc in collection.find():
        blob_name = doc.get("blob_name")
        if not blob_name:
            # Compatibilidad con documentos antiguos
            blob_name = _infer_blob_name_from_legacy_url(doc.get("image_url"))
        image_url = _build_sas_for_blob(blob_name)

        detalle = ProductoDetallePlano(
            id=str(doc.get("_id")),
            product_type=doc.get("product_type"),
            product_name=doc.get("product_name", "unknown"),
            size=doc.get("size"),
            price=float(doc.get("price", 0)),
            amount=int(doc.get("amount", 0)),
            image_url=image_url,
            blob_name=blob_name
        )
        items.append(detalle)
    return items

#@app.get("/get_productos_nested", response_model=ProductosRespuesta)
#def get_productos_nested():
#   products: Dict[str, Dict[str, Dict[str, ProductoDetalle]]] = {}
#    for doc in collection.find():
#        product_type = doc.get("product_type")
#        product_name = doc.get("product_name", "unknown")
#        size = doc.get("size")
#        blob_name = doc.get("blob_name") or _infer_blob_name_from_legacy_url(doc.get("image_url"))
#        image_url = _build_sas_for_blob(blob_name)
#        detalle = ProductoDetalle(
#            id=str(doc.get("_id")),
#            product_type=product_type,
#            size=size,
#            price=float(doc.get("price", 0)),
#            amount=int(doc.get("amount", 0)),
#            image_url=image_url,
#            blob_name=blob_name
#        )
#        if product_type not in products:
#            products[product_type] = {}
#        if product_name not in products[product_type]:
#            products[product_type][product_name] = {}
#        products[product_type][product_name][size] = detalle
#    return {"products": products}