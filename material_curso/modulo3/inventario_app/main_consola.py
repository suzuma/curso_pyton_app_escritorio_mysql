"""
Sistema de inventario en consola con POO (entregable del Módulo 2).

Ejecutar desde la carpeta inventario_app:  python main_consola.py
"""

from datetime import date, timedelta

from models.categoria import Categoria
from models.producto import Producto, ProductoPerecedero
from repositories.producto_repository import RepositorioProductos, RepositorioProductosMemoria

ELECTRONICA = Categoria("Electrónica")
OFICINA = Categoria("Oficina")
ALIMENTOS = Categoria("Alimentos")


def cargar_ejemplos(repo: RepositorioProductos) -> None:
    repo.agregar(Producto("PROD-001", "Teclado mecánico", ELECTRONICA, "85.50", 15))
    repo.agregar(Producto("PROD-002", "Monitor 24 pulgadas", ELECTRONICA, 190, 8))
    repo.agregar(Producto.desde_dict(
        {"sku": "PROD-003", "nombre": "Silla ergonómica", "categoria": "Oficina", "precio": 220, "stock": 5}
    ))
    repo.agregar(ProductoPerecedero("ALIM-001", "Café en grano 1 kg", ALIMENTOS, "249.90", 12,
                                    caducidad=date.today() + timedelta(days=90)))


def listar(repo: RepositorioProductos) -> None:
    for producto in repo.listar():
        marca = "  ⚠" if producto.stock_bajo else ""
        print(f"  {producto}{marca}")      # __str__ y descripcion() polimórfico
    total = sum((p.valor_inventario for p in repo.listar()), start=0)
    print(f"  Valor del inventario: ${total:,.2f}")


def leer_entero(mensaje: str) -> int:
    """Convierte la respuesta a entero con un mensaje de error en español."""
    texto = input(mensaje).strip()
    try:
        return int(texto)
    except ValueError:
        raise ValueError(f"'{texto}' no es un número entero.") from None


def agregar(repo: RepositorioProductos) -> None:
    try:
        producto = Producto(
            sku=input("SKU: "),
            nombre=input("Nombre: "),
            categoria=Categoria(input("Categoría: ")),
            precio=input("Precio: "),
            stock=leer_entero("Stock: "),
        )
        repo.agregar(producto)
    except ValueError as err:   # la validación vive en la clase
        print(f"  Error: {err}")
    else:
        print(f"  Agregado: {producto!r}")


def movimiento(repo: RepositorioProductos) -> None:
    producto = repo.obtener(input("SKU: "))
    if producto is None:
        print("  No existe ese producto.")
        return
    try:
        producto.ajustar_stock(leer_entero("Cantidad (+entrada / -salida): "))
    except ValueError as err:
        print(f"  Error: {err}")
    else:
        print(f"  Stock actual: {producto.stock}")


def menu() -> None:
    repo = RepositorioProductosMemoria()
    cargar_ejemplos(repo)
    acciones = {"1": listar, "2": agregar, "3": movimiento}
    while True:
        print(f"\n=== Inventario POO ({len(repo)} productos) ===")
        print("1. Listar  2. Agregar  3. Entrada/salida de stock  4. Salir")
        opcion = input("Opción: ").strip()
        if opcion == "4":
            break
        accion = acciones.get(opcion)
        if accion:
            accion(repo)
        else:
            print("  Opción no válida.")


if __name__ == "__main__":
    menu()
