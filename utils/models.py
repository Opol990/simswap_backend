from pydantic import BaseModel, Field, EmailStr
from pydantic import BaseModel
from datetime import datetime
from typing import List,Optional

#Modelos pydantic

class UserModel(BaseModel):
    username: str = Field(..., example="user123")
    password: str = Field(..., example="securepassword")
    email: str = Field(..., example="user@example.com")
    apellido1:str 
    apellido2:Optional[str]
    
    
    
    # class Config:
    #     orm_mode = True
    #     from_attributes=True

class LoginRequest(BaseModel):
    email:str
    password:str

class RegisterUserRequest(BaseModel):
    username: str = Field(..., example="nuevo_usuario")
    nombre: str = Field(..., example="nuevo_usuario")
    apellido1: str = Field(..., example="nuevo_usuario")
    apellido2: Optional[str] = Field(..., example="nuevo_usuario")
    email: EmailStr = Field(..., example="nuevo@usuario.com")
    contraseña: str = Field(..., example="contraseñaSegura123")
    ubicacion: Optional[str] = Field(None, description="Ciudad, País")
    
class UpdateUserRequest(BaseModel):
    username: str = Field(..., example="nuevo_usuario")
    nombre: str = Field(..., example="nuevo_usuario")
    email: EmailStr = Field(..., example="nuevo@usuario.com")
    apellido1: str = Field(..., example="nuevo_usuario")
    apellido2: Optional[str] = Field(..., example="nuevo_usuario")
    fecha_registro: Optional[datetime] = Field(default_factory=datetime.utcnow, example="2023-01-01T00:00:00")
    ubicacion: Optional[str] = Field(None, description="Ciudad, País")

class FindUserRequest(BaseModel):
    user_id: Optional[int] = Field(None, description="ID del usuario")
    token: Optional[str] = Field(None, description="Token del usuario")    

class ProductModel(BaseModel):
    nombre_producto: str = Field(..., example="Laptop HP Probook 450 G1")
    marca: str = Field(..., example="Laptop HP Probook 450 G1")
    modelo: str = Field(..., example="Laptop HP Probook 450 G1")
    precio: float 
    descripcion: Optional[str] = Field(None, example="Una laptop robusta y confiable para profesionales.")
    localizacion: str = Field(..., example="Madrid, España")
    categoria: str = Field(..., example="Volante, Pedalera")
    # class Config:
    #     orm_mode = True

class UpdateProduct(BaseModel):
    nombre_producto: Optional[str]
    marca: Optional[str]
    modelo: Optional[str]
    precio: Optional[float]
    descripcion: Optional[str]
    localizacion: Optional[str]
    categoria: Optional[str]  # Usamos el nombre de la categoría para buscar su id


class FindProductIDRequest(BaseModel):
    product_id: Optional[int] = Field(None, description="ID del producto")


class ProductQuery(BaseModel):
    nombre: Optional[str] = Field(None, example="Laptop HP")
    descripcion: Optional[str] = Field(None, example="robusta y confiable")
    localizacion: Optional[str] = Field(None, example="Madrid")
    categoria: Optional[str] = Field(None, example="Electrónica")


class Message(BaseModel):
    producto_id: int
    id_usuario_envia: int
    id_usuario_recibe: int
    contenido: str
    fecha_envio: datetime
    leido: Optional[bool] = False

class Review(BaseModel):
    valoracion_id: Optional[int]
    de_usuario_id: int
    para_usuario_id: int
    puntuacion: int
    comentario: Optional[str]
    fecha_valoracion: datetime

class TransactionModel(BaseModel):
    comprador_id: int
    vendedor_id: int
    producto_id: int
    monto: float
    nombre_producto: str
    stripe_payment_id : Optional[str] = ""

class Shipment(BaseModel):
    envio_id: Optional[int]
    transaccion_id: int
    estado_envio: str
    fecha_envio: Optional[datetime]