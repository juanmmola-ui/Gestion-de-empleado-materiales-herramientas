import sys
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.services.api_client import (
    obtener_personal,
    registrar_personal,
    eliminar_personal,
)


class PersonalView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        ctk.CTkLabel(
            self,
            text="Personal del Taller — Gestión de Pañol y Personal",
            font=("Arial", 18, "bold"),
        ).pack(pady=(10, 5))

        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=15, pady=5)

        self.entry_nombre = ctk.CTkEntry(form, placeholder_text="Nombre y Apellido", width=180)
        self.entry_nombre.pack(side="left", padx=5, pady=8)

        self.entry_email = ctk.CTkEntry(form, placeholder_text="Email", width=180)
        self.entry_email.pack(side="left", padx=5, pady=8)

        self.entry_dni = ctk.CTkEntry(form, placeholder_text="DNI / CUIT", width=120)
        self.entry_dni.pack(side="left", padx=5, pady=8)

        self.entry_rol = ctk.CTkEntry(form, placeholder_text="Rol / Puesto", width=140)
        self.entry_rol.pack(side="left", padx=5, pady=8)

        ctk.CTkButton(form, text="Agregar", width=95, command=self._agregar).pack(side="left", padx=5)

        self.lbl_estado = ctk.CTkLabel(self, text="")
        self.lbl_estado.pack(pady=4)

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=15, pady=10)

    def _agregar(self):
        nombre = self.entry_nombre.get().strip()
        email = self.entry_email.get().strip()
        dni = self.entry_dni.get().strip()
        rol = self.entry_rol.get().strip()

        if not nombre or not email or not dni or not rol:
            self.lbl_estado.configure(text="⚠ Completá todos los campos", text_color="#e74c3c")
            return

        res, err = registrar_personal({
            "nombre": nombre,
            "email": email,
            "dni_cuit": dni,
            "rol": rol,
        })
        if res:
            self.entry_nombre.delete(0, "end")
            self.entry_email.delete(0, "end")
            self.entry_dni.delete(0, "end")
            self.entry_rol.delete(0, "end")
            self.lbl_estado.configure(text="✓ Trabajador registrado", text_color="#2ecc71")
            self._cargar_datos()
        else:
            self.lbl_estado.configure(text=f"⚠ {err}", text_color="#e74c3c")

    def _borrar(self, personal_id: int, personal_nombre: str):
        confirmado = messagebox.askyesno(
            "Confirmar baja de trabajador",
            f"¿Estás seguro de que querés eliminar a '{personal_nombre}'?\n\n"
            "Todas las herramientas y materiales que tenía asignados volverán automáticamente al stock.",
        )
        if not confirmado:
            return

        ok, msg = eliminar_personal(personal_id)
        if ok:
            self.lbl_estado.configure(text=f"✓ {msg}", text_color="#2ecc71")
            self._cargar_datos()
        else:
            self.lbl_estado.configure(text=f"⚠ {msg}", text_color="#e74c3c")

    def _cargar_datos(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        personas, err = obtener_personal()
        if err:
            self.lbl_estado.configure(text=f"⚠ {err}", text_color="#e74c3c")
            return

        if not personas:
            ctk.CTkLabel(self.scroll, text="No hay personal registrado todavía.", text_color="gray").pack(pady=15)
            return

        for persona in personas:
            fila = ctk.CTkFrame(self.scroll)
            fila.pack(fill="x", pady=3, padx=4)

            ctk.CTkButton(
                fila,
                text="Borrar",
                width=80,
                fg_color="#e74c3c",
                hover_color="#c0392b",
                command=lambda pid=persona["id"], pnom=persona["nombre"]: self._borrar(pid, pnom),
            ).pack(side="right", padx=8, pady=5)

            texto = f"👤 {persona['nombre']} — DNI: {persona['dni_cuit']} — {persona['rol']}"
            ctk.CTkLabel(fila, text=texto, anchor="w").pack(side="left", fill="x", expand=True, padx=10, pady=6)

    def refresh(self):
        self.lbl_estado.configure(text="")
        self._cargar_datos()