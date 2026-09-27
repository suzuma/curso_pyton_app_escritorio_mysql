"""
Prueba de la capa de persistencia (entregable del Módulo 4).

Ejecutar desde la carpeta inventario_app, con MySQL en marcha y el .env listo:

    python prueba_persistencia.py

Cada prueba imprime OK o FALLA. El script deja la base como la encontró.
"""

from decimal import Decimal

from config.db_connection import DatabaseConnection, DatabaseConnectionError
from models.categoria import Categoria
from models.producto import Producto
from repositories.categoria_repository import CategoriaRepository
from repositories.exceptions import DuplicateEntryError, ForeignKeyError
from repositories.producto_repository import ProductoRepository

resultados: list[bool] = []


def verificar(descripcion: str, condicion: bool) -> None:
    resultados.append(condicion)
    print(f"{'OK   ' if condicion else 'FALLA'} {descripcion}")


def main() -> None:
    ok, mensaje = DatabaseConnection.probar_conexion()
    print(mensaje)
    if not ok:
        return

    categorias = CategoriaRepository()
    productos = ProductoRepository()

    # --- CREATE y READ ------------------------------------------------
    cat = Categoria(nombre="Prueba M4", descripcion="Categoría temporal")
    categorias.crear(cat)
    verificar("INSERT devuelve el id generado", cat.id is not None and cat.id > 0)

    prod = Producto(categoria_id=cat.id, sku="M4-001", nombre="Producto de prueba",
                    precio=Decimal("10.50"), stock=3)
    productos.crear(prod)
    leido = productos.obtener_por_id(prod.id)
    verificar("SELECT por id devuelve el mismo producto",
              leido is not None and leido.sku == "M4-001")
    verificar("El precio vuelve como Decimal exacto",
              leido is not None and leido.precio == Decimal("10.50"))
    verificar("El JOIN trae el nombre de la categoría",
              leido is not None and leido.categoria_nombre == "Prueba M4")

    # --- UPDATE --------------------------------------------------------
    prod.stock = 7
    verificar("UPDATE informa que el registro existía", productos.actualizar(prod))
    verificar("UPDATE sin cambios también informa que existía (FOUND_ROWS)",
              productos.actualizar(prod))
    verificar("El stock se actualizó", productos.obtener_por_id(prod.id).stock == 7)

    # --- Restricciones de la base -------------------------------------
    try:
        productos.crear(Producto(categoria_id=cat.id, sku="M4-001", nombre="Duplicado",
                                 precio=Decimal("1"), stock=1))
        verificar("UNIQUE en sku rechaza duplicados", False)
    except DuplicateEntryError:
        verificar("UNIQUE en sku rechaza duplicados", True)

    try:
        categorias.eliminar(cat.id)
        verificar("La FK impide borrar una categoría con productos", False)
    except ForeignKeyError:
        verificar("La FK impide borrar una categoría con productos", True)

    # --- Inyección SQL -------------------------------------------------
    ataque = "' OR '1'='1"
    verificar("Un intento de inyección se busca como texto literal",
              productos.listar(texto=ataque) == [])

    # --- Transacción: rollback ----------------------------------------
    try:
        with DatabaseConnection.obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute("UPDATE productos SET stock = %s WHERE id = %s", (999, prod.id))
            raise RuntimeError("falla simulada antes del commit")
    except RuntimeError:
        pass
    verificar("Sin commit, el cambio se revierte (rollback)",
              productos.obtener_por_id(prod.id).stock == 7)

    # --- DELETE y limpieza --------------------------------------------
    with DatabaseConnection.obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM productos WHERE id = %s", (prod.id,))
        conexion.commit()
        cursor.close()
    verificar("DELETE de la categoría ya sin productos", categorias.eliminar(cat.id))

    print(f"\n{sum(resultados)} de {len(resultados)} pruebas correctas.")


if __name__ == "__main__":
    try:
        main()
    except DatabaseConnectionError as err:
        print(f"Error de conexión: {err}")
