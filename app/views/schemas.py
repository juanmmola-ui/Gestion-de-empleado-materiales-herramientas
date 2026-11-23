from pydantic import BaseModel
from typing import Optional, List

class PersonalResponse(BaseModel):
    id: int
    nombre: str
    email: str
    dni_cuit: str
    rol: str
    estado: str
    class Config: from_attributes = True

class PersonalCreate(BaseModel):
    nombre: str
    email: str
    dni_cuit: str
    rol: str

class MaterialBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    stock: int

class MaterialResponse(MaterialBase):
    id: int
    class Config: from_attributes = True

class MaterialCreate(MaterialBase):
    pass

class DetalleItem(BaseModel):
    material_id: int
    cantidad: int

class TransaccionCreate(BaseModel):
    fecha: str
    tipo: str
    personal_id: int
    items: List[DetalleItem]

class HerramientaBase(BaseModel):
    nombre: str
    marca: str
    modelo: str
    antiguedad_anios: int
    estado_mantenimiento: Optional[str] = "Óptimo"

class HerramientaCreate(HerramientaBase):
    pass

class HerramientaResponse(HerramientaBase):
    id: int
    personal_id: Optional[int] = None  # <-- Esta es la línea clave
    class Config: from_attributes = True