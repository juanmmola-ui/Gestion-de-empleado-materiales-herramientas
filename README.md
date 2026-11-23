##### Gestión de Pañol y Personal##############################################################################################

Aplicación de escritorio para Windows diseñada para administrar de forma integral el inventario de materiales, herramientas, personal y movimientos (asignaciones y devoluciones) de un pañol técnico.

Combina una interfaz gráfica moderna en **CustomTkinter** con un backend local en **FastAPI** y base de datos **SQLite**, empaquetado como ejecutable autónomo para Windows (`gestionempleados.exe`).

---

##Características principales###########################################################

* **Gestión de Personal:**
  * Alta y listado de trabajadores (nombre, correo electrónico, DNI/CUIT y rol).
  * Consulta de materiales y herramientas asignadas a cada empleado.
  * **Baja segura con confirmación:** al eliminar un trabajador, el sistema libera automáticamente sus herramientas (volviéndolas al pañol) y reintegra al stock los materiales que tenía asignados.

* **Control de Materiales e Insumos:**
  * Registro de materiales con descripción, precio unitario y stock inicial.
  * Exportación directa del inventario actualizado a planilla Excel (`stock_panol.xlsx`).
  * **Baja con trazabilidad:** antes de eliminar un material, exporta automáticamente todo su historial de movimientos a `bajas_movimientos_panol.xlsx`.

* **Inventario de Herramientas:**
  * Registro detallado por nombre, marca, modelo, antigüedad y estado de mantenimiento.
  * Asignación rápida a un operario o devolución al pañol desde un menú desplegable.
  * Protección contra borrado accidental mediante confirmación previa y bloqueo si la herramienta se encuentra asignada.

* **Movimientos de Stock (Asignaciones y Devoluciones):**
  * Registro transaccional de entregas y reintegros con validación automática de stock disponible y actualización en tiempo real.

* **Arquitectura Autónoma:**
  * Al iniciar, la aplicación levanta un servidor local FastAPI en un puerto libre de `127.0.0.1` en segundo plano y almacena los datos de forma segura en `%LOCALAPPDATA%\GestionPanol`.

---

#####################Descarga e Instalación (Usuarios)#####################################################

No requiere tener Python ni dependencias instaladas en la computadora:

1. Ingresá a la sección **[Releases](../../releases)** de este repositorio.
2. Descargá el archivo **`Instalador_GestionPanol_v1.0.exe`**.
3. Ejecutá el instalador y seguí los pasos del asistente en pantalla.
4. Abrí el programa desde el acceso directo creado en el Escritorio o desde el menú Inicio de Windows.

> **Ubicación de los datos:** La base de datos (`panol_gestion.db`), el historial de bajas (`bajas_movimientos_panol.xlsx`) y el registro técnico (`gestion_panol.log`) se guardan automáticamente en `C:\Users\<TuUsuario>\AppData\Local\GestionPanol`.

