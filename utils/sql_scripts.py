from fastapi import HTTPException
from utils.sql_models import *
from utils.sql_connection import SessionLocal, engine
from utils.models import RegisterUserRequest, UpdateUserRequest, ProductModel, ProductQuery, AdvertisementModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
import re
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from utils.tools import create_access_token
from jose import JWTError, jwt 
from fastapi import FastAPI, Path,HTTPException, Depends,Request,status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import or_, and_

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

def user_login(email:str, pwd:str, db:Session):
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    if not pwd_context.verify(pwd, user.hash_contraseña):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    user_dict = {"email": user.email, "usuario_id": user.usuario_id}
    access_token = create_access_token(data=user_dict)
    return {"api_token": access_token}

def register_new_user(user_request: RegisterUserRequest, db: Session):
   # Verificar si el usuario ya existe
   existing_user = db.query(Usuario).filter(Usuario.email == user_request.email).first()
   if existing_user:
       raise HTTPException(status_code=400, detail="Email already registered")
   
   hashed_password = pwd_context.hash(user_request.contraseña)
   # Crear un nuevo usuario
   new_user = Usuario(
       nombre_usuario=user_request.nombre_usuario,
       email=user_request.email,
       hash_contraseña=hashed_password,
       fecha_registro=user_request.fecha_registro,
       ubicacion=user_request.ubicacion,
       intereses=user_request.intereses,
       historial=user_request.historial
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

def create_product(product: ProductModel, db: Session):
    categoria_id = buscar_id_categoria(product.categoria, db)
    new_product = Producto(
        nombre=product.nombre,
        descripcion=product.descripcion,
        visitas=product.visitas,
        localizacion=product.localizacion,
        categoria_id=categoria_id
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

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
    
    # Actualización dinámica basada en los campos proporcionados en la solicitud
    update_data = product.dict(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(db_product, key):
            setattr(db_product, key, value)

    # Si 'categoria' es una de las claves y necesita ser convertida a 'categoria_id'
    if 'categoria' in update_data:
        categoria_id = buscar_id_categoria(product.categoria, db)
        db_product.categoria_id = categoria_id

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


#----------------------------ANUNCIOS-----------------------------------


def add_anuncio(ad: AdvertisementModel, db: Session = Depends(get_db)):
    new_ad = Anuncio(
        vendedor_id=ad.vendedor_id,
        producto_id=ad.producto_id,
        precio=ad.precio,
        fecha_publicacion=ad.fecha_publicacion,
        estado=ad.estado
    )
    db.add(new_ad)
    db.commit()
    db.refresh(new_ad)
    return new_ad

def get_all_anuncios(db: Session):
    ads = db.query(Anuncio).all()
    return ads

def get_anuncio_by_id(ad_id: int, db: Session):
    ad = db.query(Anuncio).filter(Anuncio.anuncio_id == ad_id).first()
    if ad is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    return ad

def update_anuncio(ad_id: int, ad: AdvertisementModel, db: Session = Depends(get_db)):
    db_ad = db.query(Anuncio).filter(Anuncio.anuncio_id == ad_id).first()
    if db_ad is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    update_data = ad.dict(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(db_ad, key) and value is not None:
            setattr(db_ad, key, value)

    db.commit()
    db.refresh(db_ad)
    return db_ad


def delete_anuncio_by_id(ad_id: int, db: Session = Depends(get_db)):
    db_ad = db.query(Anuncio).filter(Anuncio.anuncio_id == ad_id).first()
    if not db_ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    db.delete(db_ad)
    db.commit()
    return {"message": "Advertisement deleted"}


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