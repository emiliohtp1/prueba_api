import requests
import os
from io import BytesIO
from PIL import Image

# URL de tu API (ajústala si tu API está en Render)
# Si estás corriendo la API localmente, probablemente sea "http://127.0.0.1:8000/"
API_URL = os.getenv("API_URL_RENDER", "http://127.0.0.1:8000/")


def create_dummy_image(filename="imagen_test.png"):
    """Lee la imagen local 'imagen_test.png' y la retorna como buffer y nombre de archivo."""
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"No se encontró el archivo de imagen: {filename}")
    with open(filename, "rb") as f:
        img_bytes = BytesIO(f.read())
        img_bytes.seek(0)
    return img_bytes, os.path.basename(filename)


def test_create_product_with_image():
    print(f"Probando el endpoint POST /productos en {API_URL}")

    # Crear imagen dummy
    image_buffer, image_filename = create_dummy_image()

    # Datos del producto
    data = {
        "product_type": "tshirt",
        "product_name": "basic_logo",
        "size": "M",
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
        assert "tshirt" in payload["products"]
        assert "basic_logo" in payload["products"]["tshirt"]
        assert "M" in payload["products"]["tshirt"]["basic_logo"]
        detalle = payload["products"]["tshirt"]["basic_logo"]["M"]
        print("Detalle M:", detalle)

    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud: {e}")
        if hasattr(e, "response") and e.response is not None:
            print("Código de estado HTTP:", e.response.status_code)
            print("Cuerpo de la respuesta:", e.response.text)
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")


if __name__ == "__main__":
    test_create_product_with_image() 