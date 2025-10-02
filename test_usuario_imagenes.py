import requests
import os
from io import BytesIO
from PIL import Image
import sys
import mimetypes

# URL de tu API (ajústala si tu API está en Render)
# Si estás corriendo la API localmente, probablemente sea "http://127.0.0.1:8000/"
API_URL = os.getenv("API_URL_RENDER", "http://127.0.0.1:8000/")

ALLOWED_TYPES = {"tshirt", "pant", "shirt", "belt", "cap", "shoes"}
INPUT_TYPE_MAP = {"pants": "pant"}

ALLOWED_SIZES = {"XS", "S", "M", "L", "XL", "XXL"}


def load_user_image():
    """Pide al usuario la ruta de una imagen local y devuelve (buffer, nombre, mime)."""
    while True:
        path = input("Ingresa la ruta a la imagen que deseas subir: ").strip()
        if not os.path.isfile(path):
            print("La ruta indicada no existe o no es un archivo.")
            continue
        mime, _ = mimetypes.guess_type(path)
        if mime is None:
            mime = "application/octet-stream"
        try:
            with open(path, "rb") as f:
                img_bytes = BytesIO(f.read())
                img_bytes.seek(0)
            return img_bytes, os.path.basename(path), mime
        except Exception as e:
            print(f"No se pudo leer la imagen: {e}")
            continue


def ask_product_type_and_name():
    print("Tipos permitidos: tshirt, pant (puedes escribir 'pants'), shirt, belt, cap, shoes")
    product_type_in = input("Ingresa el tipo de producto: ").strip().lower()
    product_type = INPUT_TYPE_MAP.get(product_type_in, product_type_in)
    if product_type not in ALLOWED_TYPES:
        print(f"Tipo no válido: {product_type_in}. Permitidos: {', '.join(sorted(ALLOWED_TYPES))}")
        sys.exit(1)

    product_name = input("Ingresa el nombre del producto (ej. basic_logo): ").strip()
    if not product_name:
        print("El nombre del producto no puede estar vacío.")
        sys.exit(1)

    return product_type, product_name


def ask_sizes_amounts_prices():
    pairs = []  # [(size, amount, price)]
    used_sizes = set()
    while True:
        print("Tallas permitidas: XS, S, M, L, XL, XXL")
        size = input("Ingresa la talla: ").strip().upper()
        if size not in ALLOWED_SIZES:
            print(f"Talla no válida: {size}. Permitidas: {', '.join(sorted(ALLOWED_SIZES))}")
            continue
        if size in used_sizes:
            print(f"La talla {size} ya fue agregada para este producto.")
            more_dup = input("¿Deseas intentar con otra talla? (s/n): ").strip().lower()
            if more_dup in {"s", "si", "sí"}:
                continue
            else:
                break
        # Precio obligatorio por talla
        try:
            price_input = input(f"Ingresa el precio para la talla {size} (obligatorio): ").strip()
            price = float(price_input)
            if price < 0:
                raise ValueError
        except ValueError:
            print("El precio es obligatorio y debe ser un número no negativo.")
            continue
        # Cantidad por talla
        try:
            amount_str = input("Ingresa la cantidad disponible para esa talla: ").strip()
            amount = int(amount_str)
            if amount < 0:
                raise ValueError
        except ValueError:
            print("La cantidad debe ser un entero no negativo.")
            continue

        pairs.append((size, amount, price))
        used_sizes.add(size)

        more = input("¿Deseas agregar otra talla para este producto? (s/n): ").strip().lower()
        if more not in {"s", "si", "sí"}:
            break
    return pairs


def post_and_check(image_buffer: BytesIO, image_filename: str, image_mime: str,
                   product_type: str, product_name: str, size: str, amount: int, price: float):
    data = {
        "product_type": product_type,
        "product_name": product_name,
        "size": size,
        "price": price,
        "amount": amount,
    }

    files = {"image": (image_filename, image_buffer, image_mime)}

    response = requests.post(f"{API_URL}productos", data=data, files=files)
    response.raise_for_status()
    result = response.json()
    print("Respuesta POST:", result)

    get_resp = requests.get(f"{API_URL}get_productos")
    get_resp.raise_for_status()
    payload = get_resp.json()
    assert "products" in payload
    assert product_type in payload["products"], "No se encontró el tipo en la respuesta"
    assert product_name in payload["products"][product_type], "No se encontró el nombre en la respuesta"
    assert size in payload["products"][product_type][product_name], "No se encontró la talla en la respuesta"
    detalle = payload["products"][product_type][product_name][size]
    print("Detalle GET:", detalle)


def main():
    print(f"Probando el endpoint POST /productos en {API_URL}")

    while True:
        try:
            # Solicitar imagen una vez por producto
            image_buffer, image_filename, image_mime = load_user_image()
            product_type, product_name = ask_product_type_and_name()
            size_amount_price_pairs = ask_sizes_amounts_prices()

            # Reutilizar el mismo buffer para cada POST (crear copia para evitar puntero movido)
            for size, amount, price in size_amount_price_pairs:
                # Clonar buffer para esta petición
                image_buffer.seek(0)
                cloned = BytesIO(image_buffer.read())
                cloned.seek(0)
                post_and_check(cloned, image_filename, image_mime, product_type, product_name, size, amount, price)
        except requests.exceptions.RequestException as e:
            print(f"Error al realizar la solicitud: {e}")
            if hasattr(e, "response") and e.response is not None:
                print("Código de estado HTTP:", e.response.status_code)
                print("Cuerpo de la respuesta:", e.response.text)
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")

        cont = input("\n¿Deseas iniciar otro ciclo para otro producto? (s/n): ").strip().lower()
        if cont not in {"s", "si", "sí"}:
            print("Saliendo del script.")
            break


if __name__ == "__main__":
    main() 