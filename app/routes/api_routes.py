import io
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import openpyxl
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.controllers.transacciones_controller import (
    buscar_materiales_por_nombre,
    buscar_personal_por_identificador,
    registrar_movimiento_stock,
)
from app.database import get_connection
from app.views.schemas import TransaccionCreate

router = APIRouter()

if getattr(sys, "frozen", False):
    DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "GestionPanol"
else:
    DATA_DIR = Path(__file__).resolve().parents[2]

DATA_DIR.mkdir(parents=True, exist_ok=True)
EXCEL_BAJAS_PATH = DATA_DIR / "bajas_movimientos_panol.xlsx"

ESTADOS_HERRAMIENTA_VALIDOS = {"Operativo", "Roto", "En reparación"}


class PersonalIn(BaseModel):
    nombre: str
    email: str
    dni_cuit: str
    rol: str


class UbicacionIn(BaseModel):
    nombre: str


class MaterialIn(BaseModel):
    nombre: str
    descripcion: Optional[str] = ""
    precio: float = 0.0
    stock: int = 0
    stock_minimo: int = 0
    ubicacion_id: Optional[int] = None


class MaterialUpdateIn(BaseModel):
    precio: Optional[float] = None
    agregar_stock: int = 0
    stock_minimo: Optional[int] = None


class HerramientaIn(BaseModel):
    nombre: str
    marca: str
    modelo: str
    antiguedad_anios: int = 0
    estado_mantenimiento: str = "Operativo"


def _guardar_movimientos_en_excel(material_id: int, material_nombre: str, movimientos: list[dict]):
    if EXCEL_BAJAS_PATH.exists():
        wb = openpyxl.load_workbook(EXCEL_BAJAS_PATH)
    else:
        wb = openpyxl.Workbook()

    if "Movimientos_Bajas" in wb.sheetnames:
        ws = wb["Movimientos_Bajas"]
    else:
        ws = wb.active
        ws.title = "Movimientos_Bajas"
        ws.append([
            "Fecha_Baja",
            "Material_ID",
            "Material_Nombre",
            "Transaccion_ID",
            "Tipo",
            "Fecha_Movimiento",
            "Personal_ID",
            "Personal_Nombre",
            "Cantidad",
        ])

    fecha_baja = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if movimientos:
        for mov in movimientos:
            fecha_mov = mov.get("fecha") or mov.get("fecha_hora") or "-"
            ws.append([
                fecha_baja,
                material_id,
                material_nombre,
                mov.get("transaccion_id", "-"),
                mov.get("tipo", "-"),
                fecha_mov,
                mov.get("personal_id", "-"),
                mov.get("personal_nombre") or "-",
                mov.get("cantidad", 0),
            ])
    else:
        ws.append([
            fecha_baja,
            material_id,
            material_nombre,
            "-",
            "SIN_MOVIMIENTOS",
            fecha_baja,
            "-",
            "-",
            0,
        ])

    wb.save(EXCEL_BAJAS_PATH)


# --- UBICACIONES ---
@router.get("/ubicaciones")
def get_ubicaciones():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM ubicaciones ORDER BY nombre ASC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


@router.post("/ubicaciones", status_code=201)
def create_ubicacion(data: UbicacionIn):
    nombre_limpio = data.nombre.strip()
    if not nombre_limpio:
        raise HTTPException(status_code=400, detail="El nombre de la ubicación no puede estar vacío.")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ubicaciones (nombre) VALUES (?)", (nombre_limpio,))
        conn.commit()
        return {"mensaje": "Ubicación creada", "id": cursor.lastrowid, "nombre": nombre_limpio}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Esa ubicación ya existe.")
    finally:
        conn.close()


@router.put("/ubicaciones/{ubicacion_id}")
def update_ubicacion(ubicacion_id: int, data: UbicacionIn):
    nombre_limpio = data.nombre.strip()
    if not nombre_limpio:
        raise HTTPException(status_code=400, detail="El nombre de la ubicación no puede estar vacío.")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM ubicaciones WHERE id = ?", (ubicacion_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Ubicación no encontrada.")

        cursor.execute(
            "UPDATE ubicaciones SET nombre = ? WHERE id = ?",
            (nombre_limpio, ubicacion_id),
        )
        conn.commit()
        return {"mensaje": f"Ubicación renombrada a '{nombre_limpio}'", "nombre": nombre_limpio}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Ya existe otra ubicación con ese nombre.")
    finally:
        conn.close()


@router.delete("/ubicaciones/{ubicacion_id}")
def delete_ubicacion(ubicacion_id: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM ubicaciones WHERE id = ?", (ubicacion_id,))
        ubi = cursor.fetchone()
        if not ubi:
            raise HTTPException(status_code=404, detail="Ubicación no encontrada.")

        cursor.execute(
            "UPDATE materiales SET ubicacion_id = NULL WHERE ubicacion_id = ?",
            (ubicacion_id,),
        )
        materiales_reasignados = cursor.rowcount

        cursor.execute("DELETE FROM ubicaciones WHERE id = ?", (ubicacion_id,))
        conn.commit()
        return {
            "mensaje": f"Ubicación '{ubi['nombre']}' eliminada (materiales pasados a 'Sin ubicación': {materiales_reasignados})"
        }
    finally:
        conn.close()


# --- PERSONAL ---
@router.get("/personal")
def get_all_personal():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM personal")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@router.post("/personal", status_code=201)
def create_personal(data: PersonalIn):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO personal (nombre, email, dni_cuit, rol) VALUES (?, ?, ?, ?)",
            (data.nombre, data.email, data.dni_cuit, data.rol),
        )
        conn.commit()
        return {"mensaje": "Trabajador registrado", "id": cursor.lastrowid}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="El email o DNI ya existen.")
    finally:
        conn.close()


@router.get("/personal/search")
def search_personal(email: Optional[str] = Query(None), dni: Optional[str] = Query(None)):
    query = email or dni
    if not query:
        raise HTTPException(status_code=400, detail="Debe proporcionar nombre, email o DNI.")
    persona = buscar_personal_por_identificador(query)
    if not persona:
        raise HTTPException(status_code=404, detail="Personal no encontrado.")
    return persona


@router.get("/personal/{personal_id}/resumen")
def get_resumen_personal(personal_id: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.id, m.nombre, SUM(
                CASE WHEN UPPER(c.tipo) = 'ASIGNACION' THEN d.cantidad
                     WHEN UPPER(c.tipo) = 'DEVOLUCION' THEN -d.cantidad
                     ELSE 0 END
            ) AS cantidad_actual
            FROM cabecera_transacciones c
            JOIN detalle_transacciones d ON c.id = d.transaccion_id
            JOIN materiales m ON d.material_id = m.id
            WHERE c.personal_id = ?
            GROUP BY m.id, m.nombre
            HAVING cantidad_actual > 0
            """,
            (personal_id,),
        )
        materiales = [dict(row) for row in cursor.fetchall()]

        cursor.execute(
            "SELECT id, nombre, marca, modelo FROM herramientas WHERE personal_id = ?",
            (personal_id,),
        )
        herramientas = [dict(row) for row in cursor.fetchall()]
        return {"materiales": materiales, "herramientas": herramientas}
    finally:
        conn.close()


@router.delete("/personal/{personal_id}")
def delete_personal(personal_id: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM personal WHERE id = ?", (personal_id,))
        persona = cursor.fetchone()
        if not persona:
            raise HTTPException(status_code=404, detail="Trabajador no encontrado.")

        cursor.execute(
            "UPDATE herramientas SET personal_id = NULL WHERE personal_id = ?",
            (personal_id,),
        )
        herramientas_devueltas = cursor.rowcount

        cursor.execute(
            """
            SELECT d.material_id, COALESCE(SUM(
                CASE WHEN UPPER(c.tipo) = 'ASIGNACION' THEN d.cantidad
                     WHEN UPPER(c.tipo) = 'DEVOLUCION' THEN -d.cantidad
                     ELSE 0 END
            ), 0) AS saldo
            FROM cabecera_transacciones c
            JOIN detalle_transacciones d ON c.id = d.transaccion_id
            WHERE c.personal_id = ?
            GROUP BY d.material_id
            """,
            (personal_id,),
        )
        saldos = cursor.fetchall()
        unidades_devueltas = 0
        for row in saldos:
            saldo = row["saldo"] or 0
            if saldo > 0:
                cursor.execute(
                    "UPDATE materiales SET stock = stock + ? WHERE id = ?",
                    (saldo, row["material_id"]),
                )
                unidades_devueltas += saldo

        cursor.execute(
            """
            DELETE FROM detalle_transacciones
            WHERE transaccion_id IN (
                SELECT id FROM cabecera_transacciones WHERE personal_id = ?
            )
            """,
            (personal_id,),
        )
        cursor.execute(
            "DELETE FROM cabecera_transacciones WHERE personal_id = ?",
            (personal_id,),
        )

        cursor.execute("DELETE FROM personal WHERE id = ?", (personal_id,))
        conn.commit()
        return {
            "mensaje": f"Trabajador eliminado (stock devuelto: {unidades_devueltas}, herramientas liberadas: {herramientas_devueltas})",
        }
    finally:
        conn.close()


# --- MATERIALES ---
@router.get("/materiales")
def get_all_materiales():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.id, m.nombre, m.descripcion, m.precio, m.stock,
                   COALESCE(m.stock_minimo, 0) AS stock_minimo,
                   m.ubicacion_id, COALESCE(u.nombre, '') AS ubicacion_nombre
            FROM materiales m
            LEFT JOIN ubicaciones u ON m.ubicacion_id = u.id
            ORDER BY m.nombre ASC
            """
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@router.post("/materiales", status_code=201)
def create_material(data: MaterialIn):
    if data.precio < 0 or data.stock < 0 or data.stock_minimo < 0:
        raise HTTPException(
            status_code=400,
            detail="El precio, el stock y el stock mínimo no pueden ser negativos.",
        )

    conn = get_connection()
    try:
        cursor = conn.cursor()
        ubi_val = data.ubicacion_id if (data.ubicacion_id and data.ubicacion_id > 0) else None
        cursor.execute(
            "INSERT INTO materiales (nombre, descripcion, precio, stock, stock_minimo, ubicacion_id) VALUES (?, ?, ?, ?, ?, ?)",
            (data.nombre, data.descripcion, data.precio, data.stock, data.stock_minimo, ubi_val),
        )
        conn.commit()
        return {"mensaje": "Material registrado", "id": cursor.lastrowid}
    finally:
        conn.close()


@router.put("/materiales/{material_id}")
def update_material_precio_stock(material_id: int, data: MaterialUpdateIn):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, precio, stock, COALESCE(stock_minimo, 0) AS stock_minimo FROM materiales WHERE id = ?",
            (material_id,),
        )
        mat = cursor.fetchone()
        if not mat:
            raise HTTPException(status_code=404, detail="Material no encontrado.")

        nuevo_precio = float(mat["precio"] or 0.0) if data.precio is None else float(data.precio)
        if nuevo_precio < 0:
            raise HTTPException(status_code=400, detail="El precio no puede ser negativo.")

        stock_actual = int(mat["stock"] or 0)
        nuevo_stock = stock_actual + int(data.agregar_stock or 0)
        if nuevo_stock < 0:
            raise HTTPException(
                status_code=400,
                detail=f"No se puede descontar más del stock actual ({stock_actual}).",
            )

        nuevo_stock_min = (
            int(mat["stock_minimo"] or 0)
            if data.stock_minimo is None
            else int(data.stock_minimo)
        )
        if nuevo_stock_min < 0:
            raise HTTPException(status_code=400, detail="El stock mínimo no puede ser negativo.")

        cursor.execute(
            "UPDATE materiales SET precio = ?, stock = ?, stock_minimo = ? WHERE id = ?",
            (nuevo_precio, nuevo_stock, nuevo_stock_min, material_id),
        )
        conn.commit()
        return {
            "mensaje": f"'{mat['nombre']}' actualizado (Stock: {nuevo_stock} | Mín: {nuevo_stock_min})",
            "precio": nuevo_precio,
            "stock": nuevo_stock,
            "stock_minimo": nuevo_stock_min,
        }
    finally:
        conn.close()


@router.put("/materiales/{material_id}/ubicacion")
def update_ubicacion_material(material_id: int, ubicacion_id: int = Query(0)):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        ubi_val = ubicacion_id if ubicacion_id > 0 else None
        cursor.execute(
            "UPDATE materiales SET ubicacion_id = ? WHERE id = ?",
            (ubi_val, material_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Material no encontrado.")
        conn.commit()
        return {"mensaje": "Ubicación actualizada"}
    finally:
        conn.close()


@router.get("/products/search")
def search_products(name: str = Query(..., min_length=1)):
    return buscar_materiales_por_nombre(name)


@router.delete("/materiales/{material_id}")
def delete_material(material_id: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM materiales WHERE id = ?", (material_id,))
        mat = cursor.fetchone()
        if not mat:
            raise HTTPException(status_code=404, detail="Material no encontrado.")

        cursor.execute(
            """
            SELECT c.*, c.id AS transaccion_id, d.cantidad, p.nombre AS personal_nombre
            FROM detalle_transacciones d
            JOIN cabecera_transacciones c ON d.transaccion_id = c.id
            LEFT JOIN personal p ON c.personal_id = p.id
            WHERE d.material_id = ?
            ORDER BY c.id ASC
            """,
            (material_id,),
        )
        movimientos = [dict(row) for row in cursor.fetchall()]

        _guardar_movimientos_en_excel(mat["id"], mat["nombre"], movimientos)

        cursor.execute("DELETE FROM detalle_transacciones WHERE material_id = ?", (material_id,))
        cursor.execute(
            """
            DELETE FROM cabecera_transacciones
            WHERE id NOT IN (SELECT DISTINCT transaccion_id FROM detalle_transacciones)
            """
        )

        cursor.execute("DELETE FROM materiales WHERE id = ?", (material_id,))
        conn.commit()
        return {
            "mensaje": f"Material eliminado y movimientos guardados en {EXCEL_BAJAS_PATH.name}",
        }
    finally:
        conn.close()


# --- TRANSACCIONES ---
@router.post("/transacciones", status_code=201)
def create_transaccion(data: TransaccionCreate):
    return registrar_movimiento_stock(data)


# --- HERRAMIENTAS ---
@router.get("/herramientas")
def get_herramientas():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM herramientas ORDER BY nombre ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@router.post("/herramientas", status_code=201)
def create_herramienta(data: HerramientaIn):
    estado = (data.estado_mantenimiento or "Operativo").strip()
    if estado not in ESTADOS_HERRAMIENTA_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail="Estado inválido. Usá: Operativo, Roto o En reparación.",
        )

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO herramientas (nombre, marca, modelo, antiguedad_anios, estado_mantenimiento) VALUES (?, ?, ?, ?, ?)",
            (data.nombre, data.marca, data.modelo, data.antiguedad_anios, estado),
        )
        conn.commit()
        return {"mensaje": "Herramienta registrada", "id": cursor.lastrowid}
    finally:
        conn.close()


@router.put("/herramientas/{herramienta_id}/mantenimiento")
def update_mantenimiento(herramienta_id: int, estado: str = Query(...)):
    estado_limpio = estado.strip()
    if estado_limpio not in ESTADOS_HERRAMIENTA_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail="Estado inválido. Usá: Operativo, Roto o En reparación.",
        )

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE herramientas SET estado_mantenimiento = ? WHERE id = ?",
            (estado_limpio, herramienta_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Herramienta no encontrada.")
        conn.commit()
        return {"mensaje": f"Estado actualizado a '{estado_limpio}'"}
    finally:
        conn.close()


@router.put("/herramientas/{herramienta_id}/asignar")
def asignar_herramienta_route(herramienta_id: int, personal_id: int = Query(0)):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, estado_mantenimiento FROM herramientas WHERE id = ?",
            (herramienta_id,),
        )
        herr = cursor.fetchone()
        if not herr:
            raise HTTPException(status_code=404, detail="Herramienta no encontrada.")

        estado_actual = herr["estado_mantenimiento"] or "Operativo"
        if personal_id > 0 and estado_actual != "Operativo":
            raise HTTPException(
                status_code=400,
                detail=f"No se puede asignar '{herr['nombre']}' porque está en estado '{estado_actual}'.",
            )

        val = personal_id if personal_id > 0 else None
        cursor.execute("UPDATE herramientas SET personal_id = ? WHERE id = ?", (val, herramienta_id))
        conn.commit()
        return {"mensaje": "Asignación actualizada"}
    finally:
        conn.close()


@router.delete("/herramientas/{herramienta_id}")
def delete_herramienta(herramienta_id: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, personal_id FROM herramientas WHERE id = ?",
            (herramienta_id,),
        )
        herr = cursor.fetchone()
        if not herr:
            raise HTTPException(status_code=404, detail="Herramienta no encontrada.")

        if herr["personal_id"] is not None:
            raise HTTPException(
                status_code=400,
                detail=f"No se puede borrar '{herr['nombre']}' porque está asignada.",
            )

        cursor.execute("DELETE FROM herramientas WHERE id = ?", (herramienta_id,))
        conn.commit()
        return {"mensaje": "Herramienta eliminada"}
    finally:
        conn.close()


# --- EXPORTACIÓN ---
@router.get("/exportar/stock")
def exportar_stock_excel(solo_faltantes: bool = Query(False)):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.id, m.nombre, m.descripcion,
                   COALESCE(u.nombre, 'Sin ubicación') AS ubicacion_nombre,
                   m.precio, m.stock, COALESCE(m.stock_minimo, 0) AS stock_minimo
            FROM materiales m
            LEFT JOIN ubicaciones u ON m.ubicacion_id = u.id
            ORDER BY u.nombre ASC, m.nombre ASC
            """
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Faltantes a Reponer" if solo_faltantes else "Stock Pañol"
    ws.append([
        "ID",
        "Nombre",
        "Descripción",
        "Ubicación",
        "Precio Unitario ($)",
        "Stock Actual",
        "Stock Mínimo",
        "Estado",
        "A Reponer",
        "Subtotal Actual ($)",
        "Costo Reposición ($)",
    ])

    total_actual = 0.0
    total_reposicion = 0.0

    for row in rows:
        precio = float(row["precio"] or 0.0)
        stock = int(row["stock"] or 0)
        stock_min = int(row["stock_minimo"] or 0)
        necesita_reponer = stock_min > 0 and stock <= stock_min

        if solo_faltantes and not necesita_reponer:
            continue

        a_reponer = max(1, stock_min - stock) if necesita_reponer else 0
        estado_txt = "REPONER" if necesita_reponer else "OK"
        subtotal = precio * stock
        costo_rep = precio * a_reponer

        total_actual += subtotal
        total_reposicion += costo_rep

        ws.append([
            row["id"],
            row["nombre"],
            row["descripcion"],
            row["ubicacion_nombre"],
            precio,
            stock,
            stock_min,
            estado_txt,
            a_reponer,
            subtotal,
            costo_rep,
        ])

    ws.append([])
    ws.append(["", "", "", "", "", "", "", "", "TOTALES ($)", total_actual, total_reposicion])

    file_stream = io.BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    nombre_archivo = "faltantes_panol.xlsx" if solo_faltantes else "stock_panol.xlsx"

    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"},
    )