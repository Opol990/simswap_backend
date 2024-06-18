from fastapi import HTTPException
from utils.sql_models import *
from utils.sql_connection import SessionLocal, engine
from utils.models import RegisterUserRequest, UpdateUserRequest, ProductModel, ProductQuery, UserModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
import re
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from utils.tools import create_access_token, verify_password
from jose import JWTError, jwt 
from fastapi import FastAPI, Path,HTTPException, Depends,Request,status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import or_, and_
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

def update_user(user_id: int, user: UpdateUserRequest, db: Session = Depends(get_db)):
    db_user = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    for var, value in vars(user).items():
        setattr(db_user, var, value) if value else None
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(user_id: int, db: Session):
    db_user = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted"}


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

def search_products(query: ProductQuery, db: Session ):
    query_filters = []
    
    if query.nombre:
        query_filters.append(Producto.nombre.ilike(f'%{query.nombre}%'))  #Busca en coincidencia en cualquier parte y no solo en princpio de la palabra e ignora mayusculas/minusculas
    if query.descripcion:
        query_filters.append(Producto.descripcion.ilike(f'%{query.descripcion}%'))
    if query.localizacion:
        query_filters.append(Producto.localizacion == query.localizacion)
    if query.categoria:
        categoria_id = buscar_id_categoria(query.categoria, db)
        query_filters.append(Producto.categoria_id == categoria_id)
    
    if not query_filters:
        raise HTTPException(status_code=400, detail="No search parameters provided")
    
    productos = db.query(Producto).filter(and_(*query_filters)).all()
    return productos

def buscar_id_categoria(nombre_categoria: str, db: Session) -> int:
    categoria = db.query(Categoria).filter(Categoria.nombre == nombre_categoria).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria not found")
    return categoria.categoria_id

def find_all_products(db:Session):
    print("llega")
    products = db.query(Producto).all()
    return products


def find_product_by_id(id_product:int, db:Session):
    product = db.query(Producto).filter(Producto.producto_id == id_product).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def update_product(product_id: int, product: ProductModel, db: Session = Depends(get_db)):
    db_product = db.query(Producto).filter(Producto.producto_id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    print("LLega a update_product")
    # Actualización dinámica basada en los campos proporcionados en la solicitud
    update_data = product.model_dump(exclude_unset=True)
    print("crear update_data")
    for key, value in update_data.items():
        if hasattr(db_product, key):
            setattr(db_product, key, value)
            print(f"Atributo {key} cambiado")

    # Si 'categoria' es una de las claves y necesita ser convertida a 'categoria_id'
    if 'categoria' in update_data:
        categoria_id = buscar_id_categoria(product.categoria, db)
        db_product.categoria_id = categoria_id
        print("categoria cambiada")



    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product_by_id(product_id: int, db: Session):
    db_product = db.query(Producto).filter(Producto.producto_id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(db_product)
    db.commit()
    return {"message": "Producto Borrado"}



# async def get_current_user(api_token: str = Depends(oauth2_scheme)):
#     try:
#         print("Entra")
#         payload = jwt.decode(api_token, SECRET_KEY, algorithms=[ALGORITHM])
#         print(f'------------------PAYLOAD:{payload}')
#         user = UserModel(**payload ,username=USUARIO.username,first_name= USUARIO.first_name,last_name=USUARIO.last_name)  # Crear instancia del modelo desde el payload
#         if user.username is None:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
#         return user
#     except JWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or expired token")
#     except ValidationError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token data")