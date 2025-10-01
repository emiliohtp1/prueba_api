import requests
import os
from io import BytesIO
from PIL import Image

# URL de tu API (ajústala si tu API está en Render)
# Si estás corriendo la API localmente, probablemente sea "http://127.0.0.1:8000"
API_URL = os.getenv("API_URL_RENDER", "http://127.0.0.1:8000")

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
        "size": "M",
        "price": 25.50,
        "amount": 10
    }

    # Preparar los archivos y datos para la solicitud multipart/form-data
    # Los campos de datos deben pasarse directamente a 'data' para FastAPI Form(...)
    files = {'image': (image_filename, image_buffer, 'image/png')}

    try:
        response = requests.post(f"{API_URL}productos", data=data, files=files)
        response.raise_for_status()  # Lanza una excepción para códigos de estado de error (4xx o 5xx)
        result = response.json()
        print("Respuesta exitosa:", result)
        assert "inserted_id" in result
        assert "msg" in result
        print("Producto creado con ID:", result["inserted_id"])

    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print("Código de estado HTTP:", e.response.status_code)
            print("Cuerpo de la respuesta:", e.response.text)
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    test_create_product_with_image() 