import os
import webbrowser
import requests

API_BASE_URL = os.environ.get("GESTION_PANOL_API_URL", "http://127.0.0.1:8000")
TIMEOUT = (3, 15)
HEADERS = {"Connection": "close"}


def _leer_json(resp):
    try:
        return resp.json(), None
    except Exception:
        texto = (resp.text or "").strip()
        return None, f"Respuesta inválida ({resp.status_code}): {texto[:150] or 'vacía'}"


def _extraer_error(resp, fallback: str) -> str:
    data, _ = _leer_json(resp)
    if isinstance(data, dict) and "detail" in data:
        return str(data["detail"])
    texto = (resp.text or "").strip()
    if texto:
        return f"Error ({resp.status_code}): {texto[:180]}"
    return f"{fallback} (código {resp.status_code})"


# --- UBICACIONES ---
def obtener_ubicaciones():
    try:
        resp = requests.get(
            f"{API_BASE_URL}/ubicaciones",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data, err = _leer_json(resp)
            return (data or []), err
        return [], _extraer_error(resp, "Error al cargar ubicaciones.")
    except requests.RequestException as e:
        return [], f"Error de conexión: {e}"


def crear_ubicacion(nombre: str):
    try:
        resp = requests.post(
            f"{API_BASE_URL}/ubicaciones",
            json={"nombre": nombre},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 201:
            return _leer_json(resp)
        return None, _extraer_error(resp, "Error al crear ubicación.")
    except requests.RequestException as e:
        return None, f"Error de conexión: {e}"


def actualizar_ubicacion(ubicacion_id: int, nombre: str):
    try:
        resp = requests.put(
            f"{API_BASE_URL}/ubicaciones/{ubicacion_id}",
            json={"nombre": nombre},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data, _ = _leer_json(resp)
            msg = data.get("mensaje", "Ubicación actualizada.") if isinstance(data, dict) else "Ubicación actualizada."
            return True, msg
        return False, _extraer_error(resp, "Error al renombrar ubicación.")
    except requests.RequestException as e:
        return False, f"Error de conexión: {e}"


def eliminar_ubicacion(ubicacion_id: int):
    try:
        resp = requests.delete(
            f"{API_BASE_URL}/ubicaciones/{ubicacion_id}",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data, _ = _leer_json(resp)
            msg = data.get("mensaje", "Ubicación eliminada.") if isinstance(data, dict) else "Ubicación eliminada."
            return True, msg
        return False, _extraer_error(resp, "Error al eliminar ubicación.")
    except requests.RequestException as e:
        return False, f"Error de conexión: {e}"


# --- MOVIMIENTOS / TRANSACCIONES ---
def buscar_personal(query: str):
    try:
        resp = requests.get(
            f"{API_BASE_URL}/personal/search",
            params={"email": query},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            return _leer_json(resp)
        return None, _extraer_error(resp, "Trabajador no encontrado.")
    except requests.RequestException as e:
        return None, f"Error de conexión: {e}"


def buscar_materiales(nombre: str):
    try:
        resp = requests.get(
            f"{API_BASE_URL}/products/search",
            params={"name": nombre},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data, err = _leer_json(resp)
            return (data or []), err
        return [], _extraer_error(resp, "Error en búsqueda.")
    except requests.RequestException as e:
        return [], f"Error de conexión: {e}"


def registrar_transaccion(payload: dict):
    try:
        resp = requests.post(
            f"{API_BASE_URL}/transacciones",
            json=payload,
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 201:
            return _leer_json(resp)
        return None, _extraer_error(resp, "Error al registrar movimiento.")
    except requests.RequestException as e:
        return None, f"Error de conexión: {e}"


# --- PERSONAL ---
def obtener_personal():
    try:
        resp = requests.get(
            f"{API_BASE_URL}/personal",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data, err = _leer_json(resp)
            return (data or []), err
        return [], _extraer_error(resp, "Error al cargar la lista.")
    except requests.RequestException as e:
        return [], f"Error de conexión: {e}"


def registrar_personal(payload: dict):
    try:
        resp = requests.post(
            f"{API_BASE_URL}/personal",
            json=payload,
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 201:
            return _leer_json(resp)
        return None, _extraer_error(resp, "Error al crear trabajador.")
    except requests.RequestException as e:
        return None, f"Error de conexión: {e}"


def eliminar_personal(personal_id: int):
    try:
        resp = requests.delete(
            f"{API_BASE_URL}/personal/{personal_id}",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data, _ = _leer_json(resp)
            msg = data.get("mensaje", "Trabajador eliminado.") if isinstance(data, dict) else "Trabajador eliminado."
            return True, msg
        return False, _extraer_error(resp, "No se pudo eliminar el trabajador.")
    except requests.RequestException as e:
        return False, f"Error de conexión: {e}"


def obtener_resumen_empleado(personal_id: int):
    try:
        resp = requests.get(
            f"{API_BASE_URL}/personal/{personal_id}/resumen",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            return _leer_json(resp)
        return None, _extraer_error(resp, "Error al cargar resumen.")
    except requests.RequestException as e:
        return None, f"Error de conexión: {e}"


# --- MATERIALES ---
def obtener_todos_materiales():
    try:
        resp = requests.get(
            f"{API_BASE_URL}/materiales",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data, err = _leer_json(resp)
            return (data or []), err
        return [], _extraer_error(resp, "Error al cargar materiales.")
    except requests.RequestException as e:
        return [], f"Error de conexión: {e}"


def registrar_material(payload: dict):
    try:
        resp = requests.post(
            f"{API_BASE_URL}/materiales",
            json=payload,
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 201:
            return _leer_json(resp)
        return None, _extraer_error(resp, "Error al crear material.")
    except requests.RequestException as e:
        return None, f"Error de conexión: {e}"


def actualizar_precio_stock_material(
    material_id: int,
    precio: float,
    agregar_stock: int,
    stock_minimo: int | None = None,
):
    try:
        payload = {
            "precio": precio,
            "agregar_stock": agregar_stock,
            "stock_minimo": stock_minimo,
        }
        resp = requests.put(
            f"{API_BASE_URL}/materiales/{material_id}",
            json=payload,
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data, _ = _leer_json(resp)
            msg = data.get("mensaje", "Material actualizado.") if isinstance(data, dict) else "Material actualizado."
            return True, msg
        return False, _extraer_error(resp, "Error al actualizar el material.")
    except requests.RequestException as e:
        return False, f"Error de conexión: {e}"


def actualizar_ubicacion_material(material_id: int, ubicacion_id: int):
    try:
        resp = requests.put(
            f"{API_BASE_URL}/materiales/{material_id}/ubicacion",
            params={"ubicacion_id": ubicacion_id},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            return True, None
        return False, _extraer_error(resp, "Error al actualizar ubicación.")
    except requests.RequestException as e:
        return False, f"Error de conexión: {e}"


def eliminar_material(material_id: int):
    try:
        resp = requests.delete(
            f"{API_BASE_URL}/materiales/{material_id}",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data, _ = _leer_json(resp)
            msg = data.get("mensaje", "Material eliminado.") if isinstance(data, dict) else "Material eliminado."
            return True, msg
        return False, _extraer_error(resp, "No se pudo eliminar el material.")
    except requests.RequestException as e:
        return False, f"Error de conexión: {e}"


def descargar_reporte_excel(solo_faltantes: bool = False):
    url = f"{API_BASE_URL}/exportar/stock"
    if solo_faltantes:
        url += "?solo_faltantes=true"
    webbrowser.open(url)


# --- HERRAMIENTAS ---
def obtener_herramientas():
    try:
        resp = requests.get(
            f"{API_BASE_URL}/herramientas",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data, err = _leer_json(resp)
            return (data or []), err
        return [], _extraer_error(resp, "Error al cargar herramientas.")
    except requests.RequestException as e:
        return [], f"Error de conexión: {e}"


def registrar_herramienta(payload: dict):
    try:
        resp = requests.post(
            f"{API_BASE_URL}/herramientas",
            json=payload,
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 201:
            return _leer_json(resp)
        return None, _extraer_error(resp, "Error al crear herramienta.")
    except requests.RequestException as e:
        return None, f"Error de conexión: {e}"


def eliminar_herramienta(herramienta_id: int):
    try:
        resp = requests.delete(
            f"{API_BASE_URL}/herramientas/{herramienta_id}",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data, _ = _leer_json(resp)
            msg = data.get("mensaje", "Herramienta eliminada.") if isinstance(data, dict) else "Herramienta eliminada."
            return True, msg
        return False, _extraer_error(resp, "No se pudo eliminar la herramienta.")
    except requests.RequestException as e:
        return False, f"Error de conexión: {e}"


def actualizar_mantenimiento(herramienta_id: int, estado: str):
    try:
        resp = requests.put(
            f"{API_BASE_URL}/herramientas/{herramienta_id}/mantenimiento",
            params={"estado": estado},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            return True, None
        return False, _extraer_error(resp, "Error al actualizar mantenimiento.")
    except requests.RequestException as e:
        return False, f"Error de conexión: {e}"


def asignar_herramienta(herramienta_id: int, personal_id: int):
    try:
        resp = requests.put(
            f"{API_BASE_URL}/herramientas/{herramienta_id}/asignar",
            params={"personal_id": personal_id},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            return True, None
        return False, _extraer_error(resp, "Error al asignar herramienta.")
    except requests.RequestException as e:
        return False, f"Error de conexión: {e}"