import requests
import os
from io import BytesIO
from PIL import Image
import sys

# URL de tu API (ajústala si tu API está en Render)
# Si estás corriendo la API localmente, probablemente sea "http://127.0.0.1:8000/"
API_URL = os.getenv("API_URL_RENDER", "http://127.0.0.1:8000/")

ALLOWED_TYPES = {"tshirt", "pant", "shirt", "belt", "cap", "shoes"}
INPUT_TYPE_MAP = {"pants": "pant"}

ALLOWED_SIZES = {"XS", "S", "M", "L", "XL", "XXL"}


def create_dummy_image(filename="imagen_test.png"):
    """Lee la imagen local 'imagen_test.png' y la retorna como buffer y nombre de archivo."""
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"No se encontró el archivo de imagen: {filename}")
    with open(filename, "rb") as f:
        img_bytes = BytesIO(f.read())
        img_bytes.seek(0)
    return img_bytes, os.path.basename(filename)


def get_user_input():
    print("Tipos permitidos: tshirt, pant (puedes escribir 'pants'), shirt, belt, cap, shoes")
    product_type_in = input("Ingresa el tipo de producto: ").strip().lower()

    product_type = INPUT_TYPE_MAP.get(product_type_in, product_type_in)
    if product_type not in ALLOWED_TYPES:
        print(f"Tipo no válido: {product_type_in}. Permitidos: {', '.join(sorted(ALLOWED_TYPES))}")
        sys.exit(1)

    print("Tallas permitidas: XS, S, M, L, XL, XXL")
    size = input("Ingresa la talla: ").strip().upper()
    if size not in ALLOWED_SIZES:
        print(f"Talla no válida: {size}. Permitidas: {', '.join(sorted(ALLOWED_SIZES))}")
        sys.exit(1)

    product_name = input("Ingresa el nombre del producto (ej. basic_logo): ").strip()
    if not product_name:
        print("El nombre del producto no puede estar vacío.")
        sys.exit(1)

    return product_type, size, product_name


def test_create_product_with_image():
    print(f"Probando el endpoint POST /productos en {API_URL}")

    product_type, size, product_name = get_user_input()

    # Crear imagen dummy
    image_buffer, image_filename = create_dummy_image()

    # Datos del producto
    data = {
        "product_type": product_type,
        "product_name": product_name,
        "size": size,
        "price": 25.50,
        "amount": 10,
    }

    # Preparar los archivos y datos para la solicitud multipart/form-data
    files = {"image": (image_filename, image_buffer, "image/png")}

    try:
        response = requests.post(f"{API_URL}productos", data=data, files=files)
        response.raise_for_status()
        result = response.json()
        print("Respuesta exitosa:", result)
        assert "id" in result
        assert result.get("operation") in ("inserted", "updated", "no-op")
        print("Producto afectado con ID:", result.get("id"))

        # Consultar el GET y verificar estructura
        get_resp = requests.get(f"{API_URL}get_productos")
        get_resp.raise_for_status()
        payload = get_resp.json()
        assert "products" in payload
        assert product_type in payload["products"], "No se encontró el tipo en la respuesta"
        assert product_name in payload["products"][product_type], "No se encontró el nombre en la respuesta"
        assert size in payload["products"][product_type][product_name], "No se encontró la talla en la respuesta"
        detalle = payload["products"][product_type][product_name][size]
        print("Detalle:", detalle)

    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud: {e}")
        if hasattr(e, "response") and e.response is not None:
            print("Código de estado HTTP:", e.response.status_code)
            print("Cuerpo de la respuesta:", e.response.text)
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")


if __name__ == "__main__":
    test_create_product_with_image() 