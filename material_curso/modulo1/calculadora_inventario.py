"""
Calculadora de inventario en consola (Módulo 1).

Procesa en memoria una lista de productos y calcula estadísticas.
Temas que integra: tipos de datos, control de flujo, colecciones,
comprensiones de listas, funciones con *args y **kwargs, y manejo de
excepciones.
"""

STOCK_MINIMO = 5

productos = [
    {"sku": "PROD-001", "nombre": "Teclado mecánico", "categoria": "Electrónica", "precio": 85.50, "stock": 15},
    {"sku": "PROD-002", "nombre": "Monitor 24 pulgadas", "categoria": "Electrónica", "precio": 190.00, "stock": 8},
    {"sku": "PROD-003", "nombre": "Silla ergonómica", "categoria": "Oficina", "precio": 220.00, "stock": 5},
    {"sku": "PROD-004", "nombre": "Engrapadora", "categoria": "Oficina", "precio": 12.75, "stock": 40},
]


# ---------------------------------------------------------------- estadística
def promedio(*valores):
    """Media aritmética de cualquier cantidad de números (*args)."""
    if not valores:
        raise ValueError("Se necesita al menos un valor.")
    return sum(valores) / len(valores)


def mediana(*valores):
    """Valor central de los datos ordenados."""
    if not valores:
        raise ValueError("Se necesita al menos un valor.")
    ordenados = sorted(valores)
    mitad = len(ordenados) // 2
    if len(ordenados) % 2 == 0:
        return (ordenados[mitad - 1] + ordenados[mitad]) / 2
    return ordenados[mitad]


def estadisticas(*valores):
    """Devuelve un diccionario con mínimo, máximo, promedio y mediana."""
    return {
        "mínimo": min(valores),
        "máximo": max(valores),
        "promedio": promedio(*valores),
        "mediana": mediana(*valores),
    }


# ------------------------------------------------------------------ consultas
def valor_inventario(lista):
    """Suma de precio × stock de todos los productos."""
    return sum(p["precio"] * p["stock"] for p in lista)


def stock_bajo(lista, minimo=STOCK_MINIMO):
    """Productos con stock menor o igual al mínimo (parámetro por defecto)."""
    return [p for p in lista if p["stock"] <= minimo]


def filtrar(lista, **criterios):
    """
    Filtra por cualquier campo usando **kwargs.

    Ejemplo: filtrar(productos, categoria="Oficina")
    """
    return [p for p in lista if all(p.get(campo) == valor for campo, valor in criterios.items())]


def resumen_por_categoria(lista):
    """Cantidad de productos y unidades por categoría."""
    resumen = {}
    for p in lista:
        datos = resumen.setdefault(p["categoria"], {"productos": 0, "unidades": 0})
        datos["productos"] += 1
        datos["unidades"] += p["stock"]
    return resumen


# --------------------------------------------------------------- captura
def pedir_numero(mensaje, tipo=float, minimo=0):
    """Pide un número hasta que sea válido (try / except / else)."""
    while True:
        texto = input(mensaje)
        try:
            numero = tipo(texto)
        except ValueError:
            print(f"  '{texto}' no es un número válido.")
        else:
            if numero >= minimo:
                return numero
            print(f"  El valor debe ser mayor o igual a {minimo}.")


def agregar_producto(lista):
    """Captura un producto nuevo; rechaza SKU repetidos."""
    sku = input("SKU: ").strip().upper()
    skus_existentes = {p["sku"] for p in lista}  # conjunto: búsqueda rápida
    if sku in skus_existentes:
        print("  Ya existe un producto con ese SKU.")
        return
    lista.append({
        "sku": sku,
        "nombre": input("Nombre: ").strip(),
        "categoria": input("Categoría: ").strip(),
        "precio": pedir_numero("Precio: "),
        "stock": pedir_numero("Stock: ", tipo=int),
    })
    print("  Producto agregado.")


# ------------------------------------------------------------------ salida
def mostrar(lista):
    print(f"\n{'#':>2}  {'SKU':<9} {'Nombre':<22} {'Categoría':<12} {'Precio':>9} {'Stock':>6}")
    for i, p in enumerate(lista, start=1):
        print(f"{i:>2}  {p['sku']:<9} {p['nombre']:<22} {p['categoria']:<12} "
              f"${p['precio']:>8,.2f} {p['stock']:>6}")


def menu():
    opciones = {
        "1": "Listar productos",
        "2": "Agregar producto",
        "3": "Estadísticas de precios",
        "4": "Productos con stock bajo",
        "5": "Resumen por categoría",
        "6": "Salir",
    }
    while True:
        print("\n=== Calculadora de inventario ===")
        for clave, texto in opciones.items():
            print(f"{clave}. {texto}")
        opcion = input("Opción: ").strip()

        if opcion == "1":
            mostrar(productos)
            print(f"\nValor del inventario: ${valor_inventario(productos):,.2f}")
        elif opcion == "2":
            agregar_producto(productos)
        elif opcion == "3":
            precios = [p["precio"] for p in productos]
            for nombre, valor in estadisticas(*precios).items():
                print(f"  {nombre:<9} ${valor:,.2f}")
        elif opcion == "4":
            bajos = stock_bajo(productos)
            if bajos:
                mostrar(bajos)
            else:
                print("  Ningún producto con stock bajo.")
        elif opcion == "5":
            for categoria, datos in resumen_por_categoria(productos).items():
                print(f"  {categoria:<12} {datos['productos']} productos, {datos['unidades']} unidades")
        elif opcion == "6":
            print("Hasta luego.")
            break
        else:
            print("  Opción no válida.")


if __name__ == "__main__":
    menu()
