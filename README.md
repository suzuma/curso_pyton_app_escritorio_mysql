# Sistema de Gestión de Inventario

Aplicación de escritorio en Python para administrar categorías, productos y usuarios con control de acceso por roles. Es el proyecto final del curso *Programación Integrada en Python: De la Lógica a Aplicaciones GUI y Bases de Datos*.

| | |
|---|---|
| Lenguaje | Python 3.10 o superior (probado con 3.12 y 3.14) |
| Interfaz | CustomTkinter 5.2 o superior, más `ttk.Treeview` para las tablas |
| Base de datos | MySQL 8 o MariaDB 10.6+, con `mysql-connector-python` |
| Seguridad | Consultas parametrizadas, contraseñas con bcrypt, credenciales en `.env` |
| Arquitectura | Capas: vistas → controladores → repositorios → conexión |

## Funcionalidad

- **Inicio de sesión** con bcrypt. La verificación corre en un hilo aparte para no congelar la ventana.
- **Categorías:** alta, edición, búsqueda y eliminación. No se puede eliminar una categoría que tenga productos.
- **Productos:** SKU único, precio con `Decimal`, stock no negativo, filtros por texto, categoría y estado, aviso de stock bajo y valor total del inventario.
- **Usuarios** (solo administradores): alta, cambio de rol, activación y desactivación, y restablecimiento de contraseña. Siempre debe quedar al menos un administrador activo.
- **Mi cuenta:** cada usuario cambia su propia contraseña.
- **Roles:** el *Administrador* tiene acceso a todo. El *Operador* gestiona productos, pero no puede desactivarlos ni entrar a categorías o usuarios.

## Requisitos

- Python 3.10 o superior **con Tkinter**.
  - macOS con Homebrew: `brew install python-tk@3.14` (ajuste la versión a la de su Python).
  - Ubuntu/Debian: `sudo apt install python3-tk`.
  - Windows y el instalador de python.org ya lo incluyen.
- Un servidor MySQL. La forma más sencilla es Docker (ver abajo).

## Instalación y ejecución

### 1. Configurar las credenciales

```bash
cp .env.example .env
```

Edite `.env` y cambie las contraseñas. Use solo letras, números, `_` o `-`: los caracteres `$`, `#`, comillas y espacios se interpretan de forma distinta en Docker y en Python.

| Variable | Descripción |
|---|---|
| `DB_HOST`, `DB_PORT` | Servidor MySQL. Con Docker: `127.0.0.1` y `3306`. |
| `DB_USER`, `DB_PASSWORD` | Usuario de la aplicación (no use `root`). |
| `DB_NAME` | `curso_python_db` |
| `DB_ROOT_PASSWORD` | Solo la usa Docker al crear el contenedor. |
| `DB_POOL_SIZE` | Opcional. Conexiones reutilizables, de 1 a 32 (por defecto 5). |
| `APP_THEME` | Opcional. `dark`, `light` o `system`. |

### 2. Levantar la base de datos con Docker

```bash
docker compose up -d
docker compose ps        # espere a que db muestre "healthy"
```

La primera vez se ejecuta `database/mysql_DDL.sql`, que crea las tablas y los datos de prueba. También queda disponible Adminer en <http://localhost:8080> para ver las tablas (servidor: `db`).

**Sin Docker:** ejecute `database/mysql_DDL.sql` en su servidor, cree un usuario con permisos `SELECT, INSERT, UPDATE, DELETE` sobre `curso_python_db` y ponga sus datos en `.env`.

### 3. Crear el entorno virtual e instalar dependencias

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Ejecutar

```bash
python -m config.db_connection     # prueba la conexión
python main.py
```

**Usuario inicial:** `admin@escuela.edu` / `Admin123`. Cambie la contraseña desde *Mi cuenta*.

## Generar el ejecutable

PyInstaller solo genera ejecutables para el sistema donde se ejecuta: la `.app` se genera en macOS y el `.exe` en Windows.

| Sistema | Comando | Resultado |
|---|---|---|
| macOS | `./build_mac.sh` | `dist/Inventario.app` |
| Windows | `build_windows.bat` | `dist\Inventario\Inventario.exe` |
| Linux | `python -m PyInstaller --noconfirm --clean inventario.spec` | `dist/Inventario/Inventario` |

Los scripts crean el entorno virtual si no existe, instalan `requirements-dev.txt` (que incluye PyInstaller) y compilan con `inventario.spec`.

### Dónde pone el ejecutable su `.env`

El `.env` **no se incluye en el ejecutable**, porque las credenciales podrían extraerse de él. La aplicación usa el primero que encuentre en esta lista:

1. La ruta de la variable de entorno `INVENTARIO_ENV`.
2. Junto al ejecutable: `dist/Inventario/.env` (Windows y Linux).
3. Junto a la aplicación en macOS: la carpeta que contiene `Inventario.app`.
4. La carpeta de configuración del usuario:
   - macOS: `~/Library/Application Support/Inventario/.env`
   - Windows: `%APPDATA%\Inventario\.env`
   - Linux: `~/.config/inventario/.env`

Si no encuentra ninguno, la aplicación muestra un mensaje con las rutas donde buscó.

### Notas

- **Para distribuir en Windows**, comprima la carpeta `dist\Inventario` completa; el `.exe` necesita la carpeta `_internal` que está a su lado.
- **macOS:** una `.app` compilada en su propia Mac abre sin problema. Si la envía a otra computadora, macOS la bloqueará por no estar firmada. Para abrirla, haga clic derecho y elija *Abrir*, o vaya a *Configuración del Sistema → Privacidad y seguridad → Abrir de todos modos*.
- La conexión usa la implementación en Python de `mysql-connector-python` (`use_pure=True`). Su extensión en C busca los plugins de autenticación de MySQL como bibliotecas del sistema, y PyInstaller no los incluye.

## Estructura del proyecto

```
inventario_app/
├── main.py                  Punto de entrada: prueba la BD y abre la ventana
├── config/
│   ├── settings.py          Carga del .env y constantes de la aplicación
│   └── db_connection.py     Pool de conexiones y traducción de errores
├── models/                  Entidades (dataclasses): Rol, Usuario, Categoria, Producto
├── repositories/            SQL parametrizado; BaseRepository[T] abstracta
├── controllers/             Reglas de negocio, validaciones y permisos por rol
├── views/                   Pantallas CustomTkinter (sin SQL ni conexión)
│   └── components/tabla.py  Tabla reutilizable basada en ttk.Treeview
├── utils/security.py        Hash y verificación de contraseñas (bcrypt)
├── database/mysql_DDL.sql   Creación de tablas y datos de prueba
├── docs/                    Diagramas ER y UML (ver docs/DIAGRAMAS.md)
├── docker-compose.yml       MySQL 8.4 + Adminer para desarrollo
├── inventario.spec          Configuración de PyInstaller
├── build_mac.sh / build_windows.bat
├── requirements.txt         Dependencias de la aplicación
└── requirements-dev.txt     + PyInstaller
```

La regla principal de la arquitectura es que **ninguna vista importa `mysql`, `config.db_connection` ni los repositorios**. Las vistas llaman a los controladores y solo capturan `ControllerError` y sus subclases. Los diagramas de `docs/` muestran las capas y las clases.

## Problemas frecuentes

| Mensaje | Causa y solución |
|---|---|
| `No module named '_tkinter'` | El Python no tiene Tkinter. Vea *Requisitos*. |
| `No se encontró el archivo .env…` | Cree el `.env` en alguna de las rutas indicadas en el mensaje. |
| `Usuario o contraseña de MySQL incorrectos` | El `.env` no coincide con las credenciales con que se creó el contenedor. Recréelo: `docker compose down -v && docker compose up -d`. |
| `No se pudo contactar al servidor MySQL…` | El servidor no está corriendo. Revise con `docker compose ps`. |
| `port is already allocated` (Docker) | Otro MySQL usa el puerto 3306. Cambie `DB_PORT=3307` en `.env`. |
| Acentos dañados (`ElectrÃ³nica`) | El script SQL se importó sin UTF-8. El DDL actual incluye `SET NAMES utf8mb4`; recree la base. |
