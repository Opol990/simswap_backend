from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import List, Optional

class LoginRequest(BaseModel):
    email: str = Field(..., description="Correo electrónico del usuario", example="usuario@ejemplo.com")
    password: str = Field(..., description="Contraseña del usuario", example="contraseñaSegura123")

class RegisterUserRequest(BaseModel):
    username: str = Field(..., description="Nombre de usuario", example="nuevo_usuario")
    nombre: str = Field(..., description="Nombre del usuario", example="Juan")
    apellido1: str = Field(..., description="Primer apellido del usuario", example="Pérez")
    apellido2: Optional[str] = Field(None, description="Segundo apellido del usuario", example="García")
    email: EmailStr = Field(..., description="Correo electrónico del usuario", example="nuevo@usuario.com")
    contraseña: str = Field(..., description="Contraseña para la cuenta del usuario", example="contraseñaSegura123")
    ubicacion: Optional[str] = Field(None, description="Ciudad y país del usuario", example="Madrid, España")

class UpdateUserRequest(BaseModel):
    username: str = Field(..., description="Nombre de usuario para actualización", example="usuario_actualizado")
    nombre: str = Field(..., description="Nombre del usuario", example="Juan actualizado")
    email: EmailStr = Field(..., description="Correo electrónico del usuario", example="usuario_actualizado@ejemplo.com")
    apellido1: str = Field(..., description="Primer apellido del usuario", example="Pérez actualizado")
    apellido2: Optional[str] = Field(None, description="Segundo apellido del usuario", example="García actualizado")
    fecha_registro: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Fecha de registro del usuario", example="2023-01-01T00:00:00")
    ubicacion: Optional[str] = Field(None, description="Ciudad y país del usuario", example="Barcelona, España")

class ProductModel(BaseModel):
    nombre_producto: str = Field(..., description="Nombre del producto", example="Laptop HP Probook 450 G1")
    marca: str = Field(..., description="Marca del producto", example="HP")
    modelo: str = Field(..., description="Modelo del producto", example="Probook 450 G1")
    precio: float = Field(..., description="Precio del producto en euros")
    descripcion: Optional[str] = Field(None, description="Descripción breve del producto", example="Una laptop robusta y confiable para profesionales.")
    localizacion: str = Field(..., description="Localización del producto", example="Madrid, España")
    categoria: str = Field(..., description="Categoría del producto", example="Electrónica")

class UpdateProduct(BaseModel):
    nombre_producto: Optional[str] = Field(None, description="Nombre del producto")
    marca: Optional[str] = Field(None, description="Marca del producto")
    modelo: Optional[str] = Field(None, description="Modelo del producto")
    precio: Optional[float] = Field(None, description="Precio del producto")
    descripcion: Optional[str] = Field(None, description="Descripción breve del producto")
    localizacion: Optional[str] = Field(None, description="Localización del producto")
    categoria: Optional[str] = Field(None, description="Categoría del producto")


class ProductResponse(BaseModel):
    producto_id: int = Field(..., description="Identificador único del producto")
    nombre_producto: str = Field(..., description="Nombre del producto")
    marca: str = Field(..., description="Marca del producto")
    modelo: str = Field(..., description="Modelo del producto")
    precio: float = Field(..., description="Precio del producto")
    descripcion: str = Field(..., description="Descripción del producto")
    localizacion: str = Field(..., description="Ubicación física del producto")
    categoria: str = Field(..., description="Categoría del producto")
    disponibilidad: str = Field(..., description="Estado de disponibilidad del producto")


class Message(BaseModel):
    producto_id: int = Field(..., description="ID del producto relacionado al mensaje")
    id_usuario_envia: int = Field(..., description="ID del usuario que envía el mensaje")
    id_usuario_recibe: int = Field(..., description="ID del usuario que recibe el mensaje")
    contenido: str = Field(..., description="Contenido del mensaje")
    fecha_envio: datetime = Field(..., description="Fecha de envío del mensaje")
    leido: Optional[bool] = Field(False, description="Indica si el mensaje ha sido leído")

class TransactionModel(BaseModel):
    comprador_id: int = Field(..., description="ID del comprador")
    vendedor_id: int = Field(..., description="ID del vendedor")
    producto_id: int = Field(..., description="ID del producto vendido")
    monto: float = Field(..., description="Monto de la transacción")
    nombre_producto: str = Field(..., description="Nombre del producto vendido")
    stripe_payment_id: Optional[str] = Field("", description="ID de pago de Stripe")


