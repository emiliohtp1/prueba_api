import requests

# URL de tu API en Render
url = "https://prueba-api-1kj8.onrender.com/productos"  # reemplaza con tu URL real

# Lista de productos
data = {
    "productos": [
        "pantalones",
        "playeras",
        "camisas"
    ]
}

# Hacer la petición POST
try:
    response = requests.post(url, json=data)
    response.raise_for_status()  # lanza error si hay problema
    print("Respuesta de la API:")
    print(response.json())
except requests.exceptions.RequestException as e:
    print("Error al enviar los datos:", e)
