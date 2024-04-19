from pydantic import BaseModel, Field, EmailStr
from pydantic import BaseModel
from datetime import datetime
from typing import List,Optional

#Modelos pydantic

class UserModel(BaseModel):
    username: str = Field(..., example="user123")
    password: str = Field(..., example="securepassword")
    email: str = Field(..., example="user@example.com")
    first_name:str 
    last_name:str

class LoginRequest(BaseModel):
    email:str
    password:str

class RegisterUserRequest(BaseModel):
    nombre_usuario: str = Field(..., example="nuevo_usuario")
    email: EmailStr = Field(..., example="nuevo@usuario.com")
    contraseña: str = Field(..., example="contraseñaSegura123")
    fecha_registro: Optional[datetime] = Field(default_factory=datetime.utcnow, example="2023-01-01T00:00:00")
    ubicacion: Optional[str] = Field(None, description="Ciudad, País")
    intereses: Optional[str] = Field(None, description="Simulacion, F1")
    historial: Optional[str] = Field(None, description="Historial de actividades")

class UpdateUserRequest(BaseModel):
    nombre_usuario: str = Field(..., example="nuevo_usuario")
    email: EmailStr = Field(..., example="nuevo@usuario.com")
    fecha_registro: Optional[datetime] = Field(default_factory=datetime.utcnow, example="2023-01-01T00:00:00")
    ubicacion: Optional[str] = Field(None, description="Ciudad, País")
    intereses: Optional[str] = Field(None, description="Simulacion, F1")

class FindUserRequest(BaseModel):
    user_id: Optional[int] = Field(None, description="ID del usuario")
    token: Optional[str] = Field(None, description="Token del usuario")    

class ProductModel(BaseModel):
    nombre: str = Field(..., example="Laptop HP Probook 450 G1")
    descripcion: Optional[str] = Field(None, example="Una laptop robusta y confiable para profesionales.")
    visitas: Optional[int] = Field(default=0, example=0)
    localizacion: str = Field(..., example="Madrid, España")
    categoria_id: str = Field(..., example="Volante, Pedalera")

    class Config:
        orm_mode = True

class FindProductIDRequest(BaseModel):
    user_id: Optional[int] = Field(None, description="ID del producto")


class ProductQuery(BaseModel):
    nombre: Optional[str] = Field(None, example="Laptop HP")
    descripcion: Optional[str] = Field(None, example="robusta y confiable")
    localizacion: Optional[str] = Field(None, example="Madrid")
    categoria: Optional[str] = Field(None, example="Electrónica")

    
class AdvertisementModel(BaseModel):
    vendedor_id: int = Field(..., example=1)
    producto_id: int = Field(..., example=1)
    precio: float = Field(..., example=299.99)
    fecha_publicacion: datetime = Field(default_factory=datetime.utcnow)
    estado: str = Field(default='disponible', example="disponible")

    class Config:
        orm_mode = True
