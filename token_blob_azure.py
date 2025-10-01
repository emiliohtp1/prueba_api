import os
from datetime import datetime, timedelta
from typing import Optional

from azure.storage.blob import generate_blob_sas, BlobSasPermissions

try:
    # Carga variables desde .env si existe (opcional)
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


def build_blob_sas_url(
    account_name: str,
    account_key: str,
    container_name: str,
    blob_name: str,
    expiry_minutes: int = 60,
    https_only: bool = True,
    ip_address: Optional[str] = None,
) -> str:
    """
    Genera una URL SAS de lectura (GET) para un blob privado con expiración corta.

    Parámetros:
    - account_name: Nombre de la cuenta de Storage (AZURE_STORAGE_ACCOUNT_NAME)
    - account_key: Clave de la cuenta (AZURE_STORAGE_ACCOUNT_KEY)
    - container_name: Nombre del contenedor
    - blob_name: Nombre del blob (ruta relativa dentro del contenedor)
    - expiry_minutes: Minutos de validez del SAS (por defecto 60)
    - https_only: Restringir a HTTPS (recomendado True)
    - ip_address: Limitar el acceso a una IP concreta (opcional)

    Retorna:
    - URL completa del blob con el token SAS como query string
    """
    if not account_name:
        raise ValueError("Falta 'account_name' (AZURE_STORAGE_ACCOUNT_NAME)")
    if not account_key:
        raise ValueError("Falta 'account_key' (AZURE_STORAGE_ACCOUNT_KEY)")
    if not container_name:
        raise ValueError("Falta 'container_name' (AZURE_BLOB_CONTAINER_NAME)")
    if not blob_name:
        raise ValueError("Falta 'blob_name'")

    expiry = datetime.utcnow() + timedelta(minutes=max(1, int(expiry_minutes)))

    protocol = "https" if https_only else "https,http"

    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=expiry,
        protocol=protocol,
        ip=ip_address,
    )

    base_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}"
    return f"{base_url}?{sas_token}"


def generate_sas_from_env(blob_name: Optional[str] = None, expiry_minutes: int = 60, https_only: bool = True, ip_address: Optional[str] = None) -> str:
    """
    Helper para generar la URL SAS leyendo configuración desde variables de entorno:
    - AZURE_STORAGE_ACCOUNT_NAME
    - AZURE_STORAGE_ACCOUNT_KEY
    - AZURE_BLOB_CONTAINER_NAME
    - AZURE_DEFAULT_BLOB_NAME (opcional)
    """
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME")

    # blob_name puede venir por parámetro, por env o usar un valor por defecto
    effective_blob_name = blob_name or os.getenv("AZURE_DEFAULT_BLOB_NAME") or "imagen_test.png"

    return build_blob_sas_url(
        account_name=account_name,
        account_key=account_key,
        container_name=container_name,
        blob_name=effective_blob_name,
        expiry_minutes=expiry_minutes,
        https_only=https_only,
        ip_address=ip_address,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Genera una URL SAS de lectura para un blob privado de Azure Blob Storage.")
    parser.add_argument("blob_name", nargs="?", default=None, help="Nombre del blob (p. ej.: imagenes/ejemplo.png). Si se omite, usa AZURE_DEFAULT_BLOB_NAME o 'imagen_test.png'.")
    parser.add_argument("--minutes", type=int, default=60, help="Minutos de validez del SAS (por defecto 60)")
    parser.add_argument("--http", action="store_true", help="Permitir HTTP además de HTTPS (no recomendado)")
    parser.add_argument("--ip", type=str, default=None, help="Restringir el acceso a una IP concreta (opcional)")

    args = parser.parse_args()

    try:
        url = generate_sas_from_env(
            blob_name=args.blob_name,
            expiry_minutes=args.minutes,
            https_only=not args.http,
            ip_address=args.ip,
        )
        print(url)
    except Exception as exc:
        print(f"Error generando SAS: {exc}")
        raise 