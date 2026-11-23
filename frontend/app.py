import customtkinter as ctk
from frontend.components.Sidebar import Sidebar
from frontend.views.movimientos_view import MovimientosView
from frontend.views.herramientas_view import HerramientasView
from frontend.views.personal_view import PersonalView
from frontend.views.materiales_view import MaterialesView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Pañol y Materiales Eléctricos - TECNO 3F")
        self.geometry("950x600")

        self.sidebar = Sidebar(self, on_navigate=self.mostrar_vista)
        self.sidebar.pack(side="left", fill="y")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.vistas = {
            "movimientos": MovimientosView(self.container),
            "herramientas": HerramientasView(self.container),
            "personal": PersonalView(self.container),
            "materiales": MaterialesView(self.container),
        }
        self.vista_actual = None
        self.mostrar_vista("movimientos")

    def mostrar_vista(self, nombre_vista: str):
        if nombre_vista not in self.vistas: return
        if self.vista_actual:
            self.vista_actual.pack_forget()

        nueva = self.vistas[nombre_vista]
        nueva.pack(fill="both", expand=True)
        nueva.refresh()
        self.vista_actual = nueva