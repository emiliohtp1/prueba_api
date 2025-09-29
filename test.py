import requests

# URL de tu API en Render
url = "https://prueba-api-dmoz.onrender.com/productos"  # reemplaza con tu URL real

def obtener_tipo_prenda():
    """Función para obtener el tipo de prenda del usuario"""
    tipos_validos = ["pant", "shirt", "tshirt", "cap", "belt"]
    print("\nTipos de prenda disponibles:")
    print("1. pant - Pantalones")
    print("2. shirt - Camisas")
    print("3. tshirt - Playeras")
    print("4. cap - Gorras")
    print("5. belt - Cinturones")
    
    while True:
        opcion = input("Selecciona el tipo de prenda (1-5): ").strip()
        if opcion in ["1", "2", "3", "4", "5"]:
            return tipos_validos[int(opcion) - 1]
        print("❌ Opción inválida. Por favor selecciona 1, 2, 3, 4 o 5.")

def obtener_talla():
    """Función para obtener la talla del usuario"""
    tallas_validas = ["XS", "S", "M", "G", "XG"]
    print("\nTallas disponibles: XS, S, M, G, XG")
    
    while True:
        talla = input("Ingresa la talla: ").strip().upper()
        if talla in tallas_validas:
            return talla
        print("❌ Talla inválida. Por favor ingresa: XS, S, M, G o XG")

def obtener_precio():
    """Función para obtener el precio del usuario"""
    while True:
        try:
            precio = float(input("Ingresa el precio: $"))
            if precio > 0:
                return precio
            else:
                print("❌ El precio debe ser mayor a 0.")
        except ValueError:
            print("❌ Por favor ingresa un número válido para el precio.")

def obtener_cantidad():
    """Función para obtener la cantidad del usuario"""
    while True:
        try:
            cantidad = int(input("Ingresa la cantidad: "))
            if cantidad > 0:
                return cantidad
            else:
                print("❌ La cantidad debe ser mayor a 0.")
        except ValueError:
            print("❌ Por favor ingresa un número entero válido para la cantidad.")

def crear_producto():
    """Función para crear un producto con datos del usuario"""
    print("\n" + "="*50)
    print("📝 CREAR NUEVO PRODUCTO")
    print("="*50)
    
    product_type = obtener_tipo_prenda()
    size = obtener_talla()
    price = obtener_precio()
    amount = obtener_cantidad()
    
    return {
        "product_type": product_type,
        "size": size,
        "price": price,
        "amount": amount
    }

def main():
    """Función principal para manejar la entrada de productos"""
    print("🛍️  SISTEMA DE GESTIÓN DE PRODUCTOS DE ROPA")
    print("="*50)
    
    productos = []
    
    while True:
        print(f"\nProductos agregados: {len(productos)}")
        producto = crear_producto()
        productos.append(producto)
        
        print(f"\n✅ Producto agregado:")
        print(f"   Tipo: {producto['product_type']}")
        print(f"   Talla: {producto['size']}")
        print(f"   Precio: ${producto['price']}")
        print(f"   Cantidad: {producto['amount']}")
        
        continuar = input("\n¿Deseas agregar otro producto? (s/n): ").strip().lower()
        if continuar not in ['s', 'si', 'sí', 'y', 'yes']:
            break
    
    if not productos:
        print("❌ No se agregaron productos.")
        return
    
    # Preparar datos para enviar
    data = {"productos": productos}
    
    # Mostrar resumen de productos a enviar
    print("\n" + "="*50)
    print("📋 RESUMEN DE PRODUCTOS A ENVIAR")
    print("="*50)
    for i, producto in enumerate(productos, 1):
        print(f"{i}. {producto['product_type']} - Talla: {producto['size']} - ${producto['price']} - Cantidad: {producto['amount']}")
    
    # Hacer la petición POST
    print(f"\n🚀 Enviando {len(productos)} producto(s) a la API...")
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()  # lanza error si hay problema
        print("✅ ¡Productos enviados exitosamente!")
        print("📄 Respuesta de la API:")
        print(response.json())
    except requests.exceptions.RequestException as e:
        print("❌ Error al enviar los datos:", e)

if __name__ == "__main__":
    main()
