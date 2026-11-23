from fastapi import HTTPException
from app.database import get_connection


def buscar_personal_por_identificador(query: str):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        patron = f"%{query.strip()}%"
        cursor.execute(
            """
            SELECT * FROM personal
            WHERE LOWER(email) = LOWER(?)
               OR dni_cuit = ?
               OR LOWER(nombre) LIKE LOWER(?)
               OR LOWER(email) LIKE LOWER(?)
            LIMIT 1
            """,
            (query.strip(), query.strip(), patron, patron),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def buscar_materiales_por_nombre(name: str):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        patron = f"%{name.strip()}%"
        cursor.execute(
            "SELECT * FROM materiales WHERE LOWER(nombre) LIKE LOWER(?)",
            (patron,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def registrar_movimiento_stock(data):
    conn = get_connection()
    try:
        cursor = conn.cursor()

        personal_id = getattr(data, "personal_id", None)
        tipo = (getattr(data, "tipo", "") or "").strip().upper()
        observaciones = getattr(data, "observaciones", None) or ""
        items = getattr(data, "items", None) or getattr(data, "detalles", None) or []

        if tipo not in ("ASIGNACION", "DEVOLUCION"):
            raise HTTPException(status_code=400, detail="El tipo debe ser ASIGNACION o DEVOLUCION.")

        if not items:
            raise HTTPException(status_code=400, detail="Debe incluir al menos un material.")

        cursor.execute("SELECT id, nombre FROM personal WHERE id = ?", (personal_id,))
        persona = cursor.fetchone()
        if not persona:
            raise HTTPException(status_code=404, detail="Trabajador no encontrado.")

        # Validar stock y existencia de cada material antes de guardar
        items_validados = []
        for item in items:
            mat_id = getattr(item, "material_id", None)
            cantidad = int(getattr(item, "cantidad", 0) or 0)
            if cantidad <= 0:
                raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a 0.")

            cursor.execute("SELECT id, nombre, stock FROM materiales WHERE id = ?", (mat_id,))
            mat = cursor.fetchone()
            if not mat:
                raise HTTPException(status_code=404, detail=f"Material ID {mat_id} no encontrado.")

            if tipo == "ASIGNACION" and mat["stock"] < cantidad:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente para '{mat['nombre']}' (disponible: {mat['stock']}).",
                )

            items_validados.append((mat_id, cantidad))

        # Insertar cabecera de la transacción
        cursor.execute(
            "INSERT INTO cabecera_transacciones (personal_id, tipo, observaciones) VALUES (?, ?, ?)",
            (personal_id, tipo, observaciones),
        )
        transaccion_id = cursor.lastrowid

        # Insertar detalle y actualizar stock
        for mat_id, cantidad in items_validados:
            cursor.execute(
                "INSERT INTO detalle_transacciones (transaccion_id, material_id, cantidad) VALUES (?, ?, ?)",
                (transaccion_id, mat_id, cantidad),
            )
            if tipo == "ASIGNACION":
                cursor.execute(
                    "UPDATE materiales SET stock = stock - ? WHERE id = ?",
                    (cantidad, mat_id),
                )
            else:
                cursor.execute(
                    "UPDATE materiales SET stock = stock + ? WHERE id = ?",
                    (cantidad, mat_id),
                )

        conn.commit()
        return {
            "mensaje": f"{tipo.capitalize()} registrada correctamente",
            "transaccion_id": transaccion_id,
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar movimiento: {e}")
    finally:
        conn.close()