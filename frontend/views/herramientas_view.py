import sys
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.services.api_client import (
    obtener_herramientas,
    registrar_herramienta,
    eliminar_herramienta,
    actualizar_mantenimiento,
    asignar_herramienta,
    obtener_personal,
)

ESTADOS_HERRAMIENTA = ["Operativo", "Roto", "En reparación"]

ESTILO_ESTADO = {
    "Operativo": {"icono": "🟢", "fg": "#27ae60", "btn": "#1e8449", "hover": "#196f3d"},
    "En reparación": {"icono": "🟡", "fg": "#d68910", "btn": "#b9770e", "hover": "#9c640c"},
    "Roto": {"icono": "🔴", "fg": "#c0392b", "btn": "#922b21", "hover": "#78281f"},
}


class HerramientasView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.mapa_personal = {"En Pañol (Sin asignar)": 0}
        self.id_a_etiqueta = {}
        self.todas_herramientas = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        ctk.CTkLabel(
            self,
            text="Herramientas del Pañol — Gestión de Pañol y Personal",
            font=("Arial", 18, "bold"),
        ).pack(pady=(8, 4))

        # --- BARRA 1: ALTA DE HERRAMIENTA ---
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=15, pady=4)

        self.entry_nombre = ctk.CTkEntry(form, placeholder_text="Nombre", width=165)
        self.entry_nombre.pack(side="left", padx=4, pady=8)

        self.entry_marca = ctk.CTkEntry(form, placeholder_text="Marca", width=135)
        self.entry_marca.pack(side="left", padx=4, pady=8)

        self.entry_modelo = ctk.CTkEntry(form, placeholder_text="Modelo", width=135)
        self.entry_modelo.pack(side="left", padx=4, pady=8)

        self.entry_antiguedad = ctk.CTkEntry(form, placeholder_text="Años", width=65)
        self.entry_antiguedad.pack(side="left", padx=4, pady=8)

        self.var_estado_alta = ctk.StringVar(value="Operativo")
        ctk.CTkOptionMenu(
            form,
            values=ESTADOS_HERRAMIENTA,
            variable=self.var_estado_alta,
            width=140,
        ).pack(side="left", padx=4, pady=8)

        ctk.CTkButton(form, text="Agregar", width=85, command=self._agregar).pack(side="left", padx=4)

        # --- BARRA 2: FILTRO POR ESTADO + RESUMEN ---
        barra_filtro = ctk.CTkFrame(self)
        barra_filtro.pack(fill="x", padx=15, pady=4)

        ctk.CTkLabel(barra_filtro, text="🔍 Estado:", font=("Arial", 12, "bold")).pack(
            side="left", padx=(10, 6), pady=6
        )

        self.var_filtro_estado = ctk.StringVar(value="Todos")
        ctk.CTkOptionMenu(
            barra_filtro,
            values=["Todos"] + ESTADOS_HERRAMIENTA,
            variable=self.var_filtro_estado,
            width=155,
            command=lambda _: self._renderizar_lista(),
        ).pack(side="left", padx=4, pady=6)

        self.entry_buscar = ctk.CTkEntry(
            barra_filtro,
            placeholder_text="Buscar por nombre, marca o modelo...",
            width=230,
        )
        self.entry_buscar.pack(side="left", padx=4, pady=6)
        self.entry_buscar.bind("<KeyRelease>", lambda _: self._renderizar_lista())

        self.lbl_resumen = ctk.CTkLabel(
            barra_filtro,
            text="🟢 Operativas: 0  |  🟡 En reparación: 0  |  🔴 Rotas: 0",
            font=("Arial", 12, "bold"),
        )
        self.lbl_resumen.pack(side="right", padx=12, pady=6)

        self.lbl_estado = ctk.CTkLabel(self, text="")
        self.lbl_estado.pack(pady=2)

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=15, pady=(4, 10))

    def _agregar(self):
        nombre = self.entry_nombre.get().strip()
        marca = self.entry_marca.get().strip()
        modelo = self.entry_modelo.get().strip()
        estado_inicial = self.var_estado_alta.get()

        try:
            antiguedad = int(self.entry_antiguedad.get().strip() or 0)
        except ValueError:
            self.lbl_estado.configure(text="⚠ Antigüedad inválida", text_color="#e74c3c")
            return

        if not nombre or not marca or not modelo:
            self.lbl_estado.configure(text="⚠ Completá nombre, marca y modelo", text_color="#e74c3c")
            return

        res, err = registrar_herramienta({
            "nombre": nombre,
            "marca": marca,
            "modelo": modelo,
            "antiguedad_anios": antiguedad,
            "estado_mantenimiento": estado_inicial,
        })
        if res:
            self.entry_nombre.delete(0, "end")
            self.entry_marca.delete(0, "end")
            self.entry_modelo.delete(0, "end")
            self.entry_antiguedad.delete(0, "end")
            self.var_estado_alta.set("Operativo")
            self.lbl_estado.configure(text="✓ Herramienta registrada", text_color="#2ecc71")
            self._cargar_datos()
        else:
            self.lbl_estado.configure(text=f"⚠ {err}", text_color="#e74c3c")

    def _cambiar_estado(self, herramienta_id: int, herramienta_nombre: str, nuevo_estado: str):
        ok, err = actualizar_mantenimiento(herramienta_id, nuevo_estado)
        if ok:
            self.lbl_estado.configure(
                text=f"✓ Estado de '{herramienta_nombre}' cambiado a {nuevo_estado}",
                text_color="#2ecc71",
            )
            self._cargar_datos()
        else:
            self.lbl_estado.configure(text=f"⚠ {err}", text_color="#e74c3c")
            self._cargar_datos()

    def _asignar(self, herramienta_id: int, opcion_elegida: str):
        personal_id = self.mapa_personal.get(opcion_elegida, 0)
        ok, err = asignar_herramienta(herramienta_id, personal_id)
        if ok:
            if personal_id == 0:
                self.lbl_estado.configure(text="✓ Herramienta devuelta al pañol", text_color="#2ecc71")
            else:
                self.lbl_estado.configure(text=f"✓ Herramienta asignada a {opcion_elegida}", text_color="#2ecc71")
            self._cargar_datos()
        else:
            self.lbl_estado.configure(text=f"⚠ {err}", text_color="#e74c3c")

    def _borrar(self, herramienta_id: int, herramienta_nombre: str):
        confirmado = messagebox.askyesno(
            "Confirmar baja de herramienta",
            f"¿Estás seguro de que querés borrar '{herramienta_nombre}'?\n\n"
            "Esta acción eliminará la herramienta del registro del pañol.",
        )
        if not confirmado:
            return

        ok, msg = eliminar_herramienta(herramienta_id)
        if ok:
            self.lbl_estado.configure(text=f"✓ {msg}", text_color="#2ecc71")
            self._cargar_datos()
        else:
            self.lbl_estado.configure(text=f"⚠ {msg}", text_color="#e74c3c")

    def _cargar_datos(self):
        personas, _ = obtener_personal()
        self.mapa_personal = {"En Pañol (Sin asignar)": 0}
        self.id_a_etiqueta = {}
        for p in personas:
            etiqueta = f"{p['id']} - {p['nombre']}"
            self.mapa_personal[etiqueta] = p["id"]
            self.id_a_etiqueta[p["id"]] = etiqueta

        herrs, err = obtener_herramientas()
        if err:
            self.lbl_estado.configure(text=f"⚠ {err}", text_color="#e74c3c")
            return

        self.todas_herramientas = herrs
        self._renderizar_lista()

    def _renderizar_lista(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        cant_operativas = 0
        cant_reparacion = 0
        cant_rotas = 0
        for h in self.todas_herramientas:
            est = h.get("estado_mantenimiento") or "Operativo"
            if est == "Roto":
                cant_rotas += 1
            elif est == "En reparación":
                cant_reparacion += 1
            else:
                cant_operativas += 1

        self.lbl_resumen.configure(
            text=f"🟢 Operativas: {cant_operativas}  |  🟡 En reparación: {cant_reparacion}  |  🔴 Rotas: {cant_rotas}"
        )

        filtro_est = self.var_filtro_estado.get()
        texto_busq = self.entry_buscar.get().strip().lower()

        filtradas = []
        for herr in self.todas_herramientas:
            est_actual = herr.get("estado_mantenimiento") or "Operativo"
            if est_actual not in ESTADOS_HERRAMIENTA:
                est_actual = "Operativo"

            if filtro_est != "Todos" and est_actual != filtro_est:
                continue

            if texto_busq:
                coincide = (
                    texto_busq in herr["nombre"].lower()
                    or texto_busq in herr["marca"].lower()
                    or texto_busq in herr["modelo"].lower()
                )
                if not coincide:
                    continue

            filtradas.append(herr)

        if not filtradas:
            msg = (
                "No se encontraron herramientas con ese filtro."
                if self.todas_herramientas
                else "No hay herramientas cargadas todavía."
            )
            ctk.CTkLabel(self.scroll, text=msg, text_color="gray").pack(pady=15)
            return

        opciones_personal = list(self.mapa_personal.keys())

        for herr in filtradas:
            fila = ctk.CTkFrame(self.scroll)
            fila.pack(fill="x", pady=3, padx=4)

            ctk.CTkButton(
                fila,
                text="Borrar",
                width=65,
                fg_color="#e74c3c",
                hover_color="#c0392b",
                command=lambda hid=herr["id"], hnom=herr["nombre"]: self._borrar(hid, hnom),
            ).pack(side="right", padx=(3, 8), pady=5)

            pid_actual = herr.get("personal_id")
            valor_inicial = self.id_a_etiqueta.get(pid_actual, "En Pañol (Sin asignar)")
            var_seleccion = ctk.StringVar(value=valor_inicial)

            ctk.CTkButton(
                fila,
                text="Asignar",
                width=70,
                fg_color="#2980b9",
                hover_color="#1f618d",
                command=lambda hid=herr["id"], v=var_seleccion: self._asignar(hid, v.get()),
            ).pack(side="right", padx=3, pady=5)

            ctk.CTkOptionMenu(
                fila,
                values=opciones_personal,
                variable=var_seleccion,
                width=175,
            ).pack(side="right", padx=3, pady=5)

            est_actual = herr.get("estado_mantenimiento") or "Operativo"
            if est_actual not in ESTADOS_HERRAMIENTA:
                est_actual = "Operativo"

            estilo = ESTILO_ESTADO[est_actual]
            var_estado_fila = ctk.StringVar(value=est_actual)

            ctk.CTkOptionMenu(
                fila,
                values=ESTADOS_HERRAMIENTA,
                variable=var_estado_fila,
                width=135,
                fg_color=estilo["fg"],
                button_color=estilo["btn"],
                button_hover_color=estilo["hover"],
                command=lambda nuevo_est, hid=herr["id"], hnom=herr["nombre"]: self._cambiar_estado(
                    hid, hnom, nuevo_est
                ),
            ).pack(side="right", padx=3, pady=5)

            asig_txt = (
                f"Asignada a {self.id_a_etiqueta[pid_actual]}"
                if pid_actual in self.id_a_etiqueta
                else "En Pañol"
            )
            texto = f"{estilo['icono']} {herr['nombre']} — {herr['marca']} {herr['modelo']} ({asig_txt})"
            ctk.CTkLabel(fila, text=texto, anchor="w").pack(side="left", fill="x", expand=True, padx=10, pady=6)

    def refresh(self):
        self.lbl_estado.configure(text="")
        self._cargar_datos()