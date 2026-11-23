import customtkinter as ctk

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate):
        super().__init__(master, width=200, corner_radius=0)
        self.on_navigate = on_navigate
        self.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(self, text="⚡ Pañol Eléctrico", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 30), padx=15)

        botones = [
            ("Movimientos / Stock", "movimientos"),
            ("Herramientas", "herramientas"),
            ("Trabajadores", "personal"),
            ("Materiales", "materiales"),
        ]
        for texto, vista_id in botones:
            ctk.CTkButton(
                self,
                text=texto,
                command=lambda v=vista_id: self.on_navigate(v),
                anchor="w",
                height=38
            ).pack(fill="x", padx=15, pady=5)