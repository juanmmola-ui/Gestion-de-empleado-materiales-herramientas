import sys
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.services.api_client import (
    obtener_ubicaciones,
    crear_ubicacion,
    actualizar_ubicacion,
    eliminar_ubicacion,
    registrar_material,
    obtener_todos_materiales,
    actualizar_precio_stock_material,
    actualizar_ubicacion_material,
    eliminar_material,
    descargar_reporte_excel,
)


def _formatear_plata(valor: float) -> str:
    return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class MaterialesView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.lista_ubicaciones = []
        self.mapa_ubicaciones = {"Sin ubicación": 0}
        self.id_a_ubicacion = {0: "Sin ubicación"}
        self.todos_materiales = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        ctk.CTkLabel(
            self,
            text="Materiales del Pañol — Gestión de Pañol y Personal",
            font=("Arial", 18, "bold"),
        ).pack(pady=(8, 4))

        # --- BARRA 1: CREAR / ADMINISTRAR UBICACIONES + TOTAL EN PLATA ---
        barra_sup = ctk.CTkFrame(self)
        barra_sup.pack(fill="x", padx=15, pady=4)

        self.entry_nueva_ubi = ctk.CTkEntry(
            barra_sup,
            placeholder_text="Nueva ubicación (ej: Rack A - Nivel 1 - Cajón 1 / Camioneta - Cajón 1)",
            width=330,
        )
        self.entry_nueva_ubi.pack(side="left", padx=(8, 4), pady=7)

        ctk.CTkButton(
            barra_sup,
            text="+ Crear ubicación",
            width=130,
            fg_color="#8e44ad",
            hover_color="#732d91",
            command=self._crear_ubicacion,
        ).pack(side="left", padx=4, pady=7)

        ctk.CTkButton(
            barra_sup,
            text="Administrar",
            width=100,
            fg_color="#34495e",
            hover_color="#2c3e50",
            command=self._abrir_gestor_ubicaciones,
        ).pack(side="left", padx=4, pady=7)

        self.lbl_total_plata = ctk.CTkLabel(
            barra_sup,
            text="Total en materiales: $ 0,00",
            font=("Arial", 14, "bold"),
            text_color="#2ecc71",
        )
        self.lbl_total_plata.pack(side="right", padx=12, pady=7)

        # --- BARRA 2: CARGAR MATERIAL ---
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=15, pady=4)

        self.entry_nombre = ctk.CTkEntry(form, placeholder_text="Nombre", width=140)
        self.entry_nombre.pack(side="left", padx=3, pady=8)

        self.entry_desc = ctk.CTkEntry(form, placeholder_text="Descripción", width=130)
        self.entry_desc.pack(side="left", padx=3, pady=8)

        self.var_ubi_alta = ctk.StringVar(value="Sin ubicación")
        self.menu_ubi_alta = ctk.CTkOptionMenu(
            form,
            values=["Sin ubicación"],
            variable=self.var_ubi_alta,
            width=165,
        )
        self.menu_ubi_alta.pack(side="left", padx=3, pady=8)

        self.entry_precio = ctk.CTkEntry(form, placeholder_text="Precio ($)", width=75)
        self.entry_precio.pack(side="left", padx=3, pady=8)

        self.entry_stock = ctk.CTkEntry(form, placeholder_text="Cant.", width=55)
        self.entry_stock.pack(side="left", padx=3, pady=8)

        self.entry_stock_min = ctk.CTkEntry(form, placeholder_text="Mín.", width=55)
        self.entry_stock_min.pack(side="left", padx=3, pady=8)

        ctk.CTkButton(form, text="Agregar", width=75, command=self._agregar).pack(side="left", padx=3)
        ctk.CTkButton(
            form,
            text="Descargar Excel",
            width=110,
            fg_color="#27ae60",
            hover_color="#1e8449",
            command=lambda: descargar_reporte_excel(solo_faltantes=False),
        ).pack(side="left", padx=3)

        # --- BARRA 3: FILTRO POR UBICACIÓN, SECTOR O FALTANTES ---
        barra_filtro = ctk.CTkFrame(self)
        barra_filtro.pack(fill="x", padx=15, pady=4)

        ctk.CTkLabel(barra_filtro, text="🔍 Filtrar:", font=("Arial", 12, "bold")).pack(
            side="left", padx=(10, 5), pady=6
        )

        self.var_filtro_ubi = ctk.StringVar(value="Todas las ubicaciones")
        self.menu_filtro_ubi = ctk.CTkOptionMenu(
            barra_filtro,
            values=["Todas las ubicaciones", "Sin ubicación"],
            variable=self.var_filtro_ubi,
            width=180,
            command=lambda _: self._renderizar_lista(),
        )
        self.menu_filtro_ubi.pack(side="left", padx=3, pady=6)

        self.entry_filtro_texto = ctk.CTkEntry(
            barra_filtro,
            placeholder_text="Buscar nombre o sector (ej: Camioneta)...",
            width=220,
        )
        self.entry_filtro_texto.pack(side="left", padx=3, pady=6)
        self.entry_filtro_texto.bind("<KeyRelease>", lambda _: self._renderizar_lista())

        self.var_solo_faltantes = ctk.BooleanVar(value=False)
        self.chk_faltantes = ctk.CTkCheckBox(
            barra_filtro,
            text="⚠️ Solo a reponer (0)",
            variable=self.var_solo_faltantes,
            font=("Arial", 12, "bold"),
            text_color="#f39c12",
            command=self._renderizar_lista,
        )
        self.chk_faltantes.pack(side="left", padx=(6, 4), pady=6)

        ctk.CTkButton(
            barra_filtro,
            text="Limpiar",
            width=70,
            fg_color="#7f8c8d",
            hover_color="#636e72",
            command=self._limpiar_filtros,
        ).pack(side="left", padx=3, pady=6)

        ctk.CTkButton(
            barra_filtro,
            text="Excel Faltantes",
            width=110,
            fg_color="#d35400",
            hover_color="#a04000",
            command=lambda: descargar_reporte_excel(solo_faltantes=True),
        ).pack(side="right", padx=(3, 10), pady=6)

        self.lbl_estado = ctk.CTkLabel(self, text="")
        self.lbl_estado.pack(pady=2)

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=15, pady=(4, 10))

    def _limpiar_filtros(self):
        self.var_filtro_ubi.set("Todas las ubicaciones")
        self.entry_filtro_texto.delete(0, "end")
        self.var_solo_faltantes.set(False)
        self._renderizar_lista()

    def _crear_ubicacion(self):
        nombre = self.entry_nueva_ubi.get().strip()
        if not nombre:
            self.lbl_estado.configure(text="⚠ Escribí un nombre para la ubicación", text_color="#e74c3c")
            return

        res, err = crear_ubicacion(nombre)
        if res:
            self.entry_nueva_ubi.delete(0, "end")
            self.lbl_estado.configure(text=f"✓ Ubicación '{nombre}' creada", text_color="#2ecc71")
            self._cargar_datos(seleccionar_ubicacion=nombre)
        else:
            self.lbl_estado.configure(text=f"⚠ {err}", text_color="#e74c3c")

    def _abrir_gestor_ubicaciones(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Administrar ubicaciones")
        ventana.geometry("500x380")
        ventana.resizable(False, False)
        ventana.transient(self.winfo_toplevel())
        ventana.grab_set()

        ctk.CTkLabel(
            ventana,
            text="📍 Ubicaciones creadas",
            font=("Arial", 16, "bold"),
        ).pack(pady=(12, 4))

        ctk.CTkLabel(
            ventana,
            text="Renombrá o eliminá ubicaciones. Al borrar una, sus materiales pasan a 'Sin ubicación'.",
            text_color="gray",
            font=("Arial", 11),
        ).pack(pady=(0, 6), padx=15)

        lbl_msg_modal = ctk.CTkLabel(ventana, text="")
        lbl_msg_modal.pack(pady=2)

        lista_frame = ctk.CTkScrollableFrame(ventana)
        lista_frame.pack(fill="both", expand=True, padx=15, pady=(4, 10))

        def _renombrar_ubi(ubi_id: int, nombre_actual: str):
            sub = ctk.CTkToplevel(ventana)
            sub.title("Renombrar ubicación")
            sub.geometry("410x185")
            sub.resizable(False, False)
            sub.transient(ventana)
            sub.grab_set()

            ctk.CTkLabel(
                sub,
                text="Nuevo nombre de la ubicación:",
                font=("Arial", 13, "bold"),
            ).pack(pady=(16, 8))

            entry_edit = ctk.CTkEntry(sub, width=340)
            entry_edit.insert(0, nombre_actual)
            entry_edit.pack(pady=4)

            lbl_sub_err = ctk.CTkLabel(sub, text="", text_color="#e74c3c")
            lbl_sub_err.pack(pady=2)

            def _cerrar_sub():
                sub.destroy()
                if ventana.winfo_exists():
                    ventana.grab_set()

            def _confirmar_renombre(_event=None):
                nuevo_nombre = entry_edit.get().strip()
                if not nuevo_nombre:
                    lbl_sub_err.configure(text="⚠ El nombre no puede estar vacío.")
                    return
                if nuevo_nombre == nombre_actual:
                    _cerrar_sub()
                    return

                ok, msg = actualizar_ubicacion(ubi_id, nuevo_nombre)
                if ok:
                    _cerrar_sub()
                    if self.var_ubi_alta.get() == nombre_actual:
                        self.var_ubi_alta.set(nuevo_nombre)
                    if self.var_filtro_ubi.get() == nombre_actual:
                        self.var_filtro_ubi.set(nuevo_nombre)
                    self._cargar_datos()
                    self.lbl_estado.configure(text=f"✓ {msg}", text_color="#2ecc71")
                    lbl_msg_modal.configure(text=f"✓ {msg}", text_color="#2ecc71")
                    _poblar_ubicaciones()
                else:
                    lbl_sub_err.configure(text=f"⚠ {msg}")

            entry_edit.bind("<Return>", _confirmar_renombre)
            sub.bind("<Escape>", lambda _: _cerrar_sub())
            sub.protocol("WM_DELETE_WINDOW", _cerrar_sub)

            fila_btns = ctk.CTkFrame(sub, fg_color="transparent")
            fila_btns.pack(pady=(6, 10))
            ctk.CTkButton(
                fila_btns,
                text="Guardar",
                width=110,
                fg_color="#27ae60",
                hover_color="#1e8449",
                command=_confirmar_renombre,
            ).pack(side="left", padx=6)
            ctk.CTkButton(
                fila_btns,
                text="Cancelar",
                width=95,
                fg_color="#7f8c8d",
                hover_color="#636e72",
                command=_cerrar_sub,
            ).pack(side="left", padx=6)

            entry_edit.focus_set()
            entry_edit.select_range(0, "end")

        def _borrar_ubi(ubi_id: int, nombre_ubi: str):
            confirmado = messagebox.askyesno(
                "Eliminar ubicación",
                f"¿Querés eliminar la ubicación '{nombre_ubi}'?\n\n"
                "Los materiales asignados a ella NO se borran: quedarán marcados como 'Sin ubicación'.",
                parent=ventana,
            )
            if not confirmado:
                return

            ok, msg = eliminar_ubicacion(ubi_id)
            if ok:
                self._cargar_datos()
                self.lbl_estado.configure(text=f"✓ {msg}", text_color="#2ecc71")
                lbl_msg_modal.configure(text=f"✓ {msg}", text_color="#2ecc71")
                _poblar_ubicaciones()
            else:
                lbl_msg_modal.configure(text=f"⚠ {msg}", text_color="#e74c3c")

        def _poblar_ubicaciones():
            for w in lista_frame.winfo_children():
                w.destroy()

            if not self.lista_ubicaciones:
                ctk.CTkLabel(
                    lista_frame,
                    text="Todavía no creaste ninguna ubicación.",
                    text_color="gray",
                ).pack(pady=20)
                return

            for u in self.lista_ubicaciones:
                fila = ctk.CTkFrame(lista_frame)
                fila.pack(fill="x", pady=3, padx=4)

                ctk.CTkButton(
                    fila,
                    text="Borrar",
                    width=68,
                    fg_color="#e74c3c",
                    hover_color="#c0392b",
                    command=lambda uid=u["id"], unom=u["nombre"]: _borrar_ubi(uid, unom),
                ).pack(side="right", padx=(3, 8), pady=5)

                ctk.CTkButton(
                    fila,
                    text="Renombrar",
                    width=85,
                    fg_color="#2980b9",
                    hover_color="#1f618d",
                    command=lambda uid=u["id"], unom=u["nombre"]: _renombrar_ubi(uid, unom),
                ).pack(side="right", padx=3, pady=5)

                ctk.CTkLabel(
                    fila,
                    text=f"📍 {u['nombre']}",
                    anchor="w",
                ).pack(side="left", fill="x", expand=True, padx=10, pady=6)

        _poblar_ubicaciones()

        ctk.CTkButton(
            ventana,
            text="Cerrar",
            width=110,
            fg_color="#7f8c8d",
            hover_color="#636e72",
            command=ventana.destroy,
        ).pack(pady=(0, 12))

    def _agregar(self):
        nombre = self.entry_nombre.get().strip()
        desc = self.entry_desc.get().strip()
        ubi_elegida = self.var_ubi_alta.get()
        ubicacion_id = self.mapa_ubicaciones.get(ubi_elegida, 0)

        try:
            precio = float(self.entry_precio.get().strip().replace(",", ".") or 0)
            stock = int(self.entry_stock.get().strip() or 0)
            stock_minimo = int(self.entry_stock_min.get().strip() or 0)
        except ValueError:
            self.lbl_estado.configure(text="⚠ Precio, cantidad o stock mínimo inválido", text_color="#e74c3c")
            return

        if precio < 0 or stock < 0 or stock_minimo < 0:
            self.lbl_estado.configure(text="⚠ Los valores numéricos no pueden ser negativos", text_color="#e74c3c")
            return

        if not nombre:
            self.lbl_estado.configure(text="⚠ Ingresá un nombre", text_color="#e74c3c")
            return

        res, err = registrar_material({
            "nombre": nombre,
            "descripcion": desc,
            "precio": precio,
            "stock": stock,
            "stock_minimo": stock_minimo,
            "ubicacion_id": ubicacion_id if ubicacion_id > 0 else None,
        })
        if res:
            self.entry_nombre.delete(0, "end")
            self.entry_desc.delete(0, "end")
            self.entry_precio.delete(0, "end")
            self.entry_stock.delete(0, "end")
            self.entry_stock_min.delete(0, "end")
            self.lbl_estado.configure(text="✓ Material registrado", text_color="#2ecc71")
            self._cargar_datos()
        else:
            self.lbl_estado.configure(text=f"⚠ {err}", text_color="#e74c3c")

    def _abrir_editor_precio_stock(self, mat: dict):
        material_id = mat["id"]
        material_nombre = mat["nombre"]
        precio_actual = float(mat.get("precio") or 0.0)
        stock_actual = int(mat.get("stock") or 0)
        stock_min_actual = int(mat.get("stock_minimo") or 0)

        dialogo = ctk.CTkToplevel(self)
        dialogo.title(f"Editar — {material_nombre}")
        dialogo.geometry("420x330")
        dialogo.resizable(False, False)
        dialogo.transient(self.winfo_toplevel())
        dialogo.grab_set()

        ctk.CTkLabel(
            dialogo,
            text=f"📦 {material_nombre}",
            font=("Arial", 15, "bold"),
        ).pack(pady=(14, 4), padx=15)

        fila_precio = ctk.CTkFrame(dialogo, fg_color="transparent")
        fila_precio.pack(fill="x", padx=25, pady=(10, 4))
        ctk.CTkLabel(fila_precio, text="Precio unitario ($):", width=175, anchor="w").pack(side="left")
        entry_precio = ctk.CTkEntry(fila_precio, width=160)
        entry_precio.insert(0, f"{precio_actual:.2f}")
        entry_precio.pack(side="right")

        fila_stock = ctk.CTkFrame(dialogo, fg_color="transparent")
        fila_stock.pack(fill="x", padx=25, pady=(8, 4))
        ctk.CTkLabel(fila_stock, text="Sumar / restar stock:", width=175, anchor="w").pack(side="left")
        entry_delta = ctk.CTkEntry(fila_stock, width=160)
        entry_delta.insert(0, "0")
        entry_delta.pack(side="right")

        fila_min = ctk.CTkFrame(dialogo, fg_color="transparent")
        fila_min.pack(fill="x", padx=25, pady=(8, 4))
        ctk.CTkLabel(fila_min, text="Stock mínimo (alerta):", width=175, anchor="w").pack(side="left")
        entry_min = ctk.CTkEntry(fila_min, width=160)
        entry_min.insert(0, str(stock_min_actual))
        entry_min.pack(side="right")

        lbl_preview = ctk.CTkLabel(
            dialogo,
            text=f"Stock actual: {stock_actual}  →  Nuevo stock: {stock_actual}",
            text_color="#2ecc71",
            font=("Arial", 12, "bold"),
        )
        lbl_preview.pack(pady=(8, 2))

        ctk.CTkLabel(
            dialogo,
            text="(Stock mínimo en 0 desactiva la alerta para este material)",
            text_color="gray",
            font=("Arial", 11),
        ).pack(pady=(0, 4))

        lbl_error = ctk.CTkLabel(dialogo, text="", text_color="#e74c3c")
        lbl_error.pack(pady=2)

        def _actualizar_preview(_event=None):
            txt = entry_delta.get().strip()
            if txt in ("", "-", "+"):
                lbl_preview.configure(
                    text=f"Stock actual: {stock_actual}  →  Nuevo stock: {stock_actual}",
                    text_color="#2ecc71",
                )
                return
            try:
                delta = int(txt)
                nuevo = stock_actual + delta
                if nuevo < 0:
                    lbl_preview.configure(
                        text=f"Stock actual: {stock_actual}  →  ⚠ Quedaría negativo ({nuevo})",
                        text_color="#e74c3c",
                    )
                else:
                    lbl_preview.configure(
                        text=f"Stock actual: {stock_actual}  →  Nuevo stock: {nuevo}",
                        text_color="#2ecc71",
                    )
            except ValueError:
                lbl_preview.configure(
                    text="⚠ Ingresá un número entero válido",
                    text_color="#e74c3c",
                )

        def _guardar(_event=None):
            try:
                nuevo_precio = float(entry_precio.get().strip().replace(",", "."))
                delta_stock = int(entry_delta.get().strip() or "0")
                nuevo_min = int(entry_min.get().strip() or "0")
            except ValueError:
                lbl_error.configure(text="⚠ Revisá que precio, stock y mínimo sean números válidos.")
                return

            if nuevo_precio < 0 or nuevo_min < 0:
                lbl_error.configure(text="⚠ El precio y el stock mínimo no pueden ser negativos.")
                return

            if stock_actual + delta_stock < 0:
                lbl_error.configure(text="⚠ No podés descontar más unidades de las que hay en stock.")
                return

            ok, msg = actualizar_precio_stock_material(material_id, nuevo_precio, delta_stock, nuevo_min)
            if ok:
                dialogo.destroy()
                self.lbl_estado.configure(text=f"✓ {msg}", text_color="#2ecc71")
                self._cargar_datos()
            else:
                lbl_error.configure(text=f"⚠ {msg}")

        entry_delta.bind("<KeyRelease>", _actualizar_preview)
        entry_precio.bind("<Return>", _guardar)
        entry_delta.bind("<Return>", _guardar)
        entry_min.bind("<Return>", _guardar)
        dialogo.bind("<Escape>", lambda _: dialogo.destroy())

        botones = ctk.CTkFrame(dialogo, fg_color="transparent")
        botones.pack(pady=(6, 12))

        ctk.CTkButton(
            botones,
            text="Guardar cambios",
            width=140,
            fg_color="#27ae60",
            hover_color="#1e8449",
            command=_guardar,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            botones,
            text="Cancelar",
            width=100,
            fg_color="#7f8c8d",
            hover_color="#636e72",
            command=dialogo.destroy,
        ).pack(side="left", padx=6)

        entry_delta.focus_set()
        entry_delta.select_range(0, "end")

    def _mover_material(self, material_id: int, material_nombre: str, opcion_ubicacion: str):
        ubicacion_id = self.mapa_ubicaciones.get(opcion_ubicacion, 0)
        ok, err = actualizar_ubicacion_material(material_id, ubicacion_id)
        if ok:
            self.lbl_estado.configure(
                text=f"✓ '{material_nombre}' movido a {opcion_ubicacion}",
                text_color="#2ecc71",
            )
            self._cargar_datos()
        else:
            self.lbl_estado.configure(text=f"⚠ {err}", text_color="#e74c3c")

    def _borrar(self, material_id: int, material_nombre: str):
        confirmado = messagebox.askyesno(
            "Confirmar baja de material",
            f"¿Estás seguro de que querés borrar '{material_nombre}'?\n\n"
            "Todos sus movimientos se van a guardar en 'bajas_movimientos_panol.xlsx' antes de eliminarlo.",
        )
        if not confirmado:
            return

        ok, msg = eliminar_material(material_id)
        if ok:
            self.lbl_estado.configure(text=f"✓ {msg}", text_color="#2ecc71")
            self._cargar_datos()
        else:
            self.lbl_estado.configure(text=f"⚠ {msg}", text_color="#e74c3c")

    def _cargar_datos(self, seleccionar_ubicacion: str | None = None):
        ubicaciones, err_u = obtener_ubicaciones()
        if err_u:
            self.lbl_estado.configure(text=f"⚠ {err_u}", text_color="#e74c3c")

        self.lista_ubicaciones = ubicaciones
        self.mapa_ubicaciones = {"Sin ubicación": 0}
        self.id_a_ubicacion = {0: "Sin ubicación"}
        for u in ubicaciones:
            self.mapa_ubicaciones[u["nombre"]] = u["id"]
            self.id_a_ubicacion[u["id"]] = u["nombre"]

        opciones_alta = list(self.mapa_ubicaciones.keys())
        self.menu_ubi_alta.configure(values=opciones_alta)
        if seleccionar_ubicacion and seleccionar_ubicacion in opciones_alta:
            self.var_ubi_alta.set(seleccionar_ubicacion)
        elif self.var_ubi_alta.get() not in opciones_alta:
            self.var_ubi_alta.set("Sin ubicación")

        opciones_filtro = ["Todas las ubicaciones"] + opciones_alta
        self.menu_filtro_ubi.configure(values=opciones_filtro)
        if self.var_filtro_ubi.get() not in opciones_filtro:
            self.var_filtro_ubi.set("Todas las ubicaciones")

        mats, err = obtener_todos_materiales()
        if err:
            self.lbl_estado.configure(text=f"⚠ {err}", text_color="#e74c3c")
            return

        self.todos_materiales = mats
        self._renderizar_lista()

    def _renderizar_lista(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        total_general = sum(
            float(m.get("precio") or 0) * int(m.get("stock") or 0)
            for m in self.todos_materiales
        )

        total_faltantes = sum(
            1
            for m in self.todos_materiales
            if int(m.get("stock_minimo") or 0) > 0
            and int(m.get("stock") or 0) <= int(m.get("stock_minimo") or 0)
        )
        self.chk_faltantes.configure(text=f"⚠️ Solo a reponer ({total_faltantes})")

        filtro_ubi = self.var_filtro_ubi.get()
        texto_busqueda = self.entry_filtro_texto.get().strip().lower()
        solo_faltantes = self.var_solo_faltantes.get()

        filtrados = []
        for mat in self.todos_materiales:
            ubi_nombre = (mat.get("ubicacion_nombre") or "").strip() or "Sin ubicación"
            stock_val = int(mat.get("stock") or 0)
            stock_min_val = int(mat.get("stock_minimo") or 0)
            necesita_reponer = stock_min_val > 0 and stock_val <= stock_min_val

            if solo_faltantes and not necesita_reponer:
                continue

            if filtro_ubi != "Todas las ubicaciones" and ubi_nombre != filtro_ubi:
                continue

            if texto_busqueda:
                hay_coincidencia = (
                    texto_busqueda in mat["nombre"].lower()
                    or texto_busqueda in (mat.get("descripcion") or "").lower()
                    or texto_busqueda in ubi_nombre.lower()
                )
                if not hay_coincidencia:
                    continue

            filtrados.append(mat)

        total_filtrado = sum(
            float(m.get("precio") or 0) * int(m.get("stock") or 0)
            for m in filtrados
        )

        hay_filtro_activo = (
            (filtro_ubi != "Todas las ubicaciones")
            or bool(texto_busqueda)
            or solo_faltantes
        )
        if hay_filtro_activo:
            self.lbl_total_plata.configure(
                text=f"Filtrado: {_formatear_plata(total_filtrado)}  |  Total Pañol: {_formatear_plata(total_general)}"
            )
        else:
            self.lbl_total_plata.configure(
                text=f"Total en materiales: {_formatear_plata(total_general)}"
            )

        if not filtrados:
            msg_vacio = (
                "No se encontraron materiales con ese filtro."
                if self.todos_materiales
                else "No hay materiales cargados todavía."
            )
            ctk.CTkLabel(self.scroll, text=msg_vacio, text_color="gray").pack(pady=15)
            return

        opciones_ubicacion = list(self.mapa_ubicaciones.keys())

        for mat in filtrados:
            precio = float(mat.get("precio") or 0)
            stock = int(mat.get("stock") or 0)
            stock_min = int(mat.get("stock_minimo") or 0)
            necesita_reponer = stock_min > 0 and stock <= stock_min

            if necesita_reponer:
                borde = "#e74c3c" if stock == 0 else "#e67e22"
                fila = ctk.CTkFrame(self.scroll, border_width=2, border_color=borde)
            else:
                fila = ctk.CTkFrame(self.scroll)
            fila.pack(fill="x", pady=3, padx=4)

            ctk.CTkButton(
                fila,
                text="Borrar",
                width=65,
                fg_color="#e74c3c",
                hover_color="#c0392b",
                command=lambda mid=mat["id"], mnom=mat["nombre"]: self._borrar(mid, mnom),
            ).pack(side="right", padx=(3, 8), pady=5)

            ctk.CTkButton(
                fila,
                text="Editar",
                width=65,
                fg_color="#d35400",
                hover_color="#a04000",
                command=lambda m=mat: self._abrir_editor_precio_stock(m),
            ).pack(side="right", padx=3, pady=5)

            ubi_actual = (mat.get("ubicacion_nombre") or "").strip() or "Sin ubicación"
            var_fila_ubi = ctk.StringVar(value=ubi_actual)

            ctk.CTkButton(
                fila,
                text="Mover",
                width=65,
                fg_color="#2980b9",
                hover_color="#1f618d",
                command=lambda mid=mat["id"], mnom=mat["nombre"], v=var_fila_ubi: self._mover_material(
                    mid, mnom, v.get()
                ),
            ).pack(side="right", padx=3, pady=5)

            ctk.CTkOptionMenu(
                fila,
                values=opciones_ubicacion,
                variable=var_fila_ubi,
                width=170,
            ).pack(side="right", padx=3, pady=5)

            subtotal = precio * stock
            desc = f" ({mat['descripcion']})" if mat.get("descripcion") else ""

            if necesita_reponer:
                prefijo = "🚨 SIN STOCK" if stock == 0 else "⚠️ REPONER"
                min_txt = f" [{prefijo} | Mín: {stock_min}]"
            elif stock_min > 0:
                min_txt = f" (Mín: {stock_min})"
            else:
                min_txt = ""

            texto = (
                f"📦 {mat['nombre']}{desc} — 📍 {ubi_actual} — "
                f"Cant: {stock}{min_txt} × {_formatear_plata(precio)} = {_formatear_plata(subtotal)}"
            )
            ctk.CTkLabel(fila, text=texto, anchor="w").pack(side="left", fill="x", expand=True, padx=10, pady=6)

    def refresh(self):
        self.lbl_estado.configure(text="")
        self._cargar_datos()