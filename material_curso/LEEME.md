# Material del curso · soluciones de referencia

Código de referencia de cada módulo del *Manual del curso: Programación Integrada en Python*.
Es material para el instructor: conviene entregarlo a los alumnos después de cada entrega.

| Carpeta | Contenido | Cómo ejecutarlo |
|---|---|---|
| `modulo1/` | Calculadora de inventario en consola | `python calculadora_inventario.py` |
| `modulo2/inventario_app/` | Inventario POO en consola: `models/`, `repositories/` en memoria | `python main_consola.py` |
| `modulo3/inventario_app/` | Pantalla de productos en CustomTkinter con datos en memoria | `python main_gui.py` |
| `modulo4/inventario_app/` | Capa de persistencia con MySQL y prueba de 12 casos | `docker compose up -d` y `python prueba_persistencia.py` |
| `modulo5/inventario_app/` | Proyecto final completo (ver su `README.md`) | `python main.py` |

Todos los comandos se ejecutan desde la carpeta indicada, con el entorno virtual activo.
Los módulos 3 a 5 necesitan `pip install -r requirements.txt` (módulo 3: `pip install customtkinter`).
Los módulos 4 y 5 necesitan un `.env` creado a partir de `.env.example`.
