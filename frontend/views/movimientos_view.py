import customtkinter as ctk
from datetime import datetime
from frontend.services.api_client import (
    buscar_personal, buscar_materiales, registrar_transaccion, obtener_resumen_empleado
)

class MovimientosView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.personal_actual = None
        self.carrito = [] # Guardará los ítems a mover
        self._build_ui()

    def _build_ui(self):
        # Layout a dos columnas
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- COLUMNA IZQUIERDA: TRABAJADOR E INVENTARIO ---
        frame_izq = ctk.CTkFrame(self)
        frame_izq.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_izq, text="1. Seleccionar Trabajador", font=("Arial", 16, "bold")).pack(pady=10)
        
        search_frame = ctk.CTkFrame(frame_izq, fg_color="transparent")
        search_frame.pack(fill="x", padx=10)
        self.entry_busqueda_pers = ctk.CTkEntry(search_frame, placeholder_text="Nombre, DNI o Email")
        self.entry_busqueda_pers.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(search_frame, text="Buscar", width=60, command=self._buscar_personal).pack(side="left")

        self.lbl_personal_info = ctk.CTkLabel(frame_izq, text="Ningún trabajador seleccionado.", text_color="gray")
        self.lbl_personal_info.pack(pady=10)

        ctk.CTkLabel(frame_izq, text="Materiales y Herramientas en su poder:", font=("Arial", 14, "bold")).pack(pady=5)
        self.scroll_inventario = ctk.CTkScrollableFrame(frame_izq, height=250)
        self.scroll_inventario.pack(fill="both", expand=True, padx=10, pady=5)


        # --- COLUMNA DERECHA: CARRITO ---
        frame_der = ctk.CTkFrame(self)
        frame_der.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_der, text="2. Agregar al Carrito", font=("Arial", 16, "bold")).pack(pady=10)
        
        search_mat_frame = ctk.CTkFrame(frame_der, fg_color="transparent")
        search_mat_frame.pack(fill="x", padx=10)
        self.entry_busqueda_mat = ctk.CTkEntry(search_mat_frame, placeholder_text="Buscar material")
        self.entry_busqueda_mat.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(search_mat_frame, text="Buscar", width=60, command=self._buscar_materiales).pack(side="left")

        self.combo_materiales = ctk.CTkOptionMenu(frame_der, values=["Buscar material primero..."])
        self.combo_materiales.pack(fill="x", padx=10, pady=10)
        
        self.entry_cantidad = ctk.CTkEntry(frame_der, placeholder_text="Cantidad")
        self.entry_cantidad.pack(pady=5)
        ctk.CTkButton(frame_der, text="Añadir a la lista", command=self._agregar_al_carrito).pack(pady=5)

        ctk.CTkLabel(frame_der, text="3. Lista de Movimiento", font=("Arial", 14, "bold")).pack(pady=10)
        self.scroll_carrito = ctk.CTkScrollableFrame(frame_der, height=150)
        self.scroll_carrito.pack(fill="both", expand=True, padx=10)

        # Confirmación
        checkout_frame = ctk.CTkFrame(frame_der, fg_color="transparent")
        checkout_frame.pack(fill="x", padx=10, pady=10)
        self.combo_tipo_mov = ctk.CTkOptionMenu(checkout_frame, values=["ASIGNACION", "DEVOLUCION", "COMPRA"], width=130)
        self.combo_tipo_mov.pack(side="left", padx=5)
        ctk.CTkButton(checkout_frame, text="Registrar", fg_color="green", command=self._registrar_movimiento).pack(side="right", padx=5)

        self.lbl_estado = ctk.CTkLabel(frame_der, text="")
        self.lbl_estado.pack(pady=5)

        self.materiales_buscados = {}

    def _buscar_personal(self):
        query = self.entry_busqueda_pers.get().strip()
        if not query: return
        persona, err = buscar_personal(query)
        if persona:
            self.personal_actual = persona
            self.lbl_personal_info.configure(text=f"👤 {persona['nombre']}", text_color="#2ecc71")
            self._cargar_inventario_personal()
        else:
            self.personal_actual = None
            self.lbl_personal_info.configure(text="Trabajador no encontrado.", text_color="#e74c3c")
            self._limpiar_inventario()

    def _cargar_inventario_personal(self):
        self._limpiar_inventario()
        if not self.personal_actual: return
        resumen, err = obtener_resumen_empleado(self.personal_actual["id"])
        
        tiene_algo = False
        if resumen:
            # Mostrar materiales
            if resumen.get("materiales"):
                tiene_algo = True
                for mat in resumen["materiales"]:
                    ctk.CTkLabel(self.scroll_inventario, text=f"📦 {mat['cantidad_actual']}x {mat['nombre']}").pack(anchor="w", padx=5, pady=2)
            
            # Mostrar herramientas (¡Ahora sí bien indentado adentro de la función!)
            if resumen.get("herramientas"):
                tiene_algo = True
                for herr in resumen["herramientas"]:
                    ctk.CTkLabel(self.scroll_inventario, text=f"🔧 {herr['nombre']} {herr['marca']} ({herr['modelo']})").pack(anchor="w", padx=5, pady=2)

        if not tiene_algo:
            ctk.CTkLabel(self.scroll_inventario, text="Pañol al día. No tiene ítems asignados.", text_color="gray").pack(anchor="w", padx=5)

    def _limpiar_inventario(self):
        for widget in self.scroll_inventario.winfo_children(): widget.destroy()

    def _buscar_materiales(self):
        query = self.entry_busqueda_mat.get().strip()
        if not query: return
        mats, err = buscar_materiales(query)
        if mats:
            self.materiales_buscados = {f"{m['nombre']} (Stock: {m['stock']})": m['id'] for m in mats}
            self.combo_materiales.configure(values=list(self.materiales_buscados.keys()))
            self.combo_materiales.set(list(self.materiales_buscados.keys())[0])

    def _agregar_al_carrito(self):
        seleccion = self.combo_materiales.get()
        if seleccion not in self.materiales_buscados: return
        
        try:
            cantidad = int(self.entry_cantidad.get().strip())
            if cantidad <= 0: raise ValueError
        except:
            self.lbl_estado.configure(text="⚠ Cantidad inválida", text_color="#e74c3c")
            return

        mat_id = self.materiales_buscados[seleccion]
        nombre = seleccion.split(" (")[0]
        self.carrito.append({"id": mat_id, "nombre": nombre, "cantidad": cantidad})
        self._dibujar_carrito()
        self.entry_cantidad.delete(0, 'end')

    def _borrar_del_carrito(self, index):
        self.carrito.pop(index)
        self._dibujar_carrito()

    def _dibujar_carrito(self):
        for widget in self.scroll_carrito.winfo_children(): widget.destroy()
        # Nota: el scroll_carrito es para el carrito, no para el inventario
        # Re-creamos los widgets del carrito correctamente
        pass # Se dibuja abajo en su propio contenedor si es necesario, 
        # pero para mantener simple: dibujamos en el scroll_carrito de la derecha:
    
    # Sobrescribimos correctamente el dibujado del carrito derecho:
    def _dibujar_carrito(self):
        for widget in self.scroll_carrito.winfo_children(): widget.destroy()
        for i, item in enumerate(self.carrito):
            row = ctk.CTkFrame(self.scroll_carrito)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{item['cantidad']}x {item['nombre']}").pack(side="left", padx=10)
            ctk.CTkButton(row, text="X", width=25, fg_color="#e74c3c", command=lambda idx=i: self._borrar_del_carrito(idx)).pack(side="right", padx=5)

    def _registrar_movimiento(self):
        if not self.personal_actual:
            self.lbl_estado.configure(text="⚠ Fije un trabajador primero.", text_color="#e74c3c")
            return
        if not self.carrito:
            self.lbl_estado.configure(text="⚠ El carrito está vacío.", text_color="#e74c3c")
            return

        payload = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tipo": self.combo_tipo_mov.get(),
            "personal_id": self.personal_actual["id"],
            "items": [{"material_id": c["id"], "cantidad": c["cantidad"]} for c in self.carrito]
        }

        res, err = registrar_transaccion(payload)
        if res:
            self.lbl_estado.configure(text="✓ Transacción registrada", text_color="#2ecc71")
            self.carrito.clear()
            self._dibujar_carrito()
            self._cargar_inventario_personal()
        else:
            self.lbl_estado.configure(text=f"⚠ Error: {err}", text_color="#e74c3c")

    def refresh(self):
        self.lbl_estado.configure(text="")