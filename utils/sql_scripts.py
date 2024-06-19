from typing import List
from fastapi import HTTPException
from utils.sql_models import *
from utils.sql_connection import SessionLocal
from utils.models import ProductResponse, RegisterUserRequest, ProductModel
from sqlalchemy.orm import Session

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from utils.tools import create_access_token, verify_password
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#----------------------------USER-----------------------------------

def user_login(email: str, pwd: str, db: Session):
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if user is None or not verify_password(pwd, user.hash_contraseña):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"email": user.email})
    return access_token, user

def register_new_user(user_request: RegisterUserRequest, db: Session):
   # Verificar si el usuario ya existe
   existing_user = db.query(Usuario).filter(Usuario.email == user_request.email).first()
   if existing_user:
       raise HTTPException(status_code=400, detail="Email already registered")
   
   hashed_password = pwd_context.hash(user_request.contraseña)
   # Crear un nuevo usuario
   new_user = Usuario(
       username = user_request.username,
       nombre=user_request.nombre,
       apellido1=user_request.apellido1,
       apellido2=user_request.apellido2,
       email=user_request.email,
       hash_contraseña=hashed_password,
       fecha_registro = datetime.now(),
       ubicacion = user_request.ubicacion
    )
   db.add(new_user)
   db.commit()
   db.refresh(new_user)
   return new_user

def get_user_by_id(user_id: int, db: Session):
    db_user = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

def update_user_info(user_id: int, user_data, db: Session):
    # Obtener el usuario actual de la base de datos
    db_user = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Actualizar los campos del usuario si se proporcionan nuevos valores
    db_user.username = user_data.username or db_user.username
    db_user.nombre = user_data.nombre or db_user.nombre
    db_user.apellido1 = user_data.apellido1 or db_user.apellido1
    db_user.apellido2 = user_data.apellido2 or db_user.apellido2
    db_user.email = user_data.email or db_user.email
    db_user.fecha_registro = user_data.fecha_registro or db_user.fecha_registro
    db_user.ubicacion = user_data.ubicacion or db_user.ubicacion

    # Guardar los cambios en la base de datos
    db.commit()
    db.refresh(db_user)
    return db_user




#----------------------------PRODUCT-----------------------------------

def create_product(product: ProductModel, user:Usuario, db: Session):
    try:
        # Buscar el categoria_id correspondiente al nombre de la categoría
        category = db.query(Categoria).filter(Categoria.nombre == product.categoria).first()
        if not category:
            raise HTTPException(status_code=400, detail="Categoría no encontrada")
        
        db_product = Producto(
            nombre_producto=product.nombre_producto,
            marca=product.marca,
            modelo=product.modelo,
            descripcion=product.descripcion,
            precio=product.precio,
            disponibilidad="disponible",
            localizacion=product.localizacion,
            categoria_id=category.categoria_id,
            vendedor_id=user.usuario_id,
            fecha_publicacion=datetime.utcnow(),
        )
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    

def get_user_products(user_id: int, db: Session) -> List[ProductResponse]:
    products = db.query(Producto).filter(Producto.vendedor_id == user_id).all()
    return [
        ProductResponse(
            producto_id=product.producto_id,
            nombre_producto=product.nombre_producto,
            marca=product.marca,
            modelo=product.modelo,
            precio=product.precio,
            descripcion=product.descripcion,
            localizacion=product.localizacion,
            categoria=product.categoria.nombre if product.categoria else "",
            disponibilidad=product.disponibilidad
        )
        for product in products
    ]


def get_products_by_category(category_name: str, user_id: int, db: Session):
    products = db.query(Producto).join(Categoria).filter(
        Categoria.nombre == category_name,
        Producto.vendedor_id != user_id,  # Excluir productos del propio usuario
        Producto.disponibilidad == 'disponible'   # Solo productos disponibles
    ).all()
    
    return products

def update_product(product_id: int, product_data, db: Session):
    db_product = db.query(Producto).filter(Producto.producto_id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Actualiza los campos del producto
    for key, value in product_data.dict().items():
        if key == "categoria":
            category = db.query(Categoria).filter(Categoria.nombre == value).first()
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")
            db_product.categoria_id = category.categoria_id
        else:
            setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product
    

def buscar_id_categoria(nombre_categoria: str, db: Session) -> int:
    categoria = db.query(Categoria).filter(Categoria.nombre == nombre_categoria).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria not found")
    return categoria.categoria_id




def find_product_by_id(id_product:int, db:Session):
    product = db.query(Producto).filter(Producto.producto_id == id_product).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product





def delete_product_by_id(product_id: int, db: Session):
    db_product = db.query(Producto).filter(Producto.producto_id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(db_product)
    db.commit()
    return {"message": "Producto Borrado"}


def create_message(message_data, db: Session):
    db_message = Mensaje(
        producto_id=message_data.producto_id,
        id_usuario_envia=message_data.id_usuario_envia,
        id_usuario_recibe=message_data.id_usuario_recibe,
        contenido=message_data.contenido,
        fecha_envio=message_data.fecha_envio,
        leido=message_data.leido
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_messages(product_id: int, user1_id: int, user2_id: int, db: Session):
    return db.query(Mensaje).filter(
        Mensaje.producto_id == product_id,
        ((Mensaje.id_usuario_envia == user1_id) & (Mensaje.id_usuario_recibe == user2_id)) |
        ((Mensaje.id_usuario_envia == user2_id) & (Mensaje.id_usuario_recibe == user1_id))
    ).all()

def get_user_messages(user_id: int, db: Session):
    messages = db.query(Mensaje).filter(
        (Mensaje.id_usuario_envia == user_id) | (Mensaje.id_usuario_recibe == user_id)
    ).all()
    if not messages:
        raise HTTPException(status_code=404, detail="No messages found for this user")
    return messages

def mark_messages_read(product_id: int, user1_id: int, user2_id: int, db: Session):
    messages = db.query(Mensaje).filter(
        Mensaje.producto_id == product_id,
        Mensaje.id_usuario_envia == user2_id,
        Mensaje.id_usuario_recibe == user1_id,
        Mensaje.leido == False
    ).all()
    
    for message in messages:
        message.leido = True
    
    db.commit()

