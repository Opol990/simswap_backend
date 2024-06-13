import logging
from fastapi import FastAPI, Path,HTTPException, Depends,Request,status
from pydantic import BaseModel, ValidationError
from typing import List,Optional
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt 
from datetime import datetime, timedelta

from sqlalchemy import Transaction
from utils.models import Message, Review, Shipment, TransactionModel, UserModel, LoginRequest, RegisterUserRequest, FindUserRequest, UpdateUserRequest, ProductModel, ProductQuery
from utils.sql_scripts import *
from utils.sql_connection import Base, engine
from utils.tools import create_access_token
from dotenv import load_dotenv
import os
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

app = FastAPI()

origins = ["*"]

Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bypass_routes = ["/docs", "/openapi.json", "/redoc", "/users/login", "/users/signup", ]

#Middleware
@app.middleware("http")
async def verify_jwt(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path in bypass_routes:
        return await call_next(request)

    authorization: str = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    scheme, _, token = authorization.partition(' ')
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme.")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Verificar que el usuario existe en la base de datos
        with SessionLocal() as db:
            user = db.query(Usuario).filter(Usuario.email == email).first()
            if user is None:
                raise HTTPException(status_code=401, detail="User not found")
            request.state.user = user
            request.state.authenticated = True

    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")

    response = await call_next(request)
    return response


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Usuario:
    if hasattr(request.state, "authenticated") and request.state.authenticated:
        return request.state.user

    token = request.headers.get("Authorization")
    if token is None or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token = token.split(" ")[1]
    email = verify_jwt(token)
    
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")
    
    return user


# # Users
@app.post("/users/signup")
async def register_user(user: RegisterUserRequest,  db: Session = Depends(get_db)):
    user_info = register_new_user(user_request=user, db=db)
    return user_info

@app.post("/users/login")
async def login_for_access_token(item: LoginRequest, db: Session = Depends(get_db)):
    access_token, user = user_login(email=item.email, pwd=item.password, db=db)
    
    user_data = {
        "id": user.usuario_id,
        "username": user.username,
        "email": user.email,
    }
    
    return {"token": access_token, "user": user_data}
@app.get("/users/me")
async def find_user_by_id(user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if user:    
        return get_user_by_id(user.usuario_id, db)

@app.put("/users/me")
async def update_user_info(user_data: UpdateUserRequest, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(Usuario).filter(Usuario.usuario_id == user.usuario_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.username = user_data.username or db_user.username
    db_user.nombre = user_data.nombre or db_user.nombre
    db_user.apellido1 = user_data.apellido1 or db_user.apellido1
    db_user.apellido2 = user_data.apellido2 or db_user.apellido2
    db_user.email = user_data.email or db_user.email
    db_user.fecha_registro = user_data.fecha_registro or db_user.fecha_registro
    db_user.ubicacion = user_data.ubicacion or db_user.ubicacion

    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}")
async def delete_user_by_id(user_id:int, db: Session = Depends(get_db)):
    message_deleted = delete_user(user_id, db)
    return {"message_deleted": message_deleted}



# Products
@app.post("/products/")
async def add_product(product: ProductModel, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    product = create_product(product, user, db)
    return product  

@app.get("/users/{user_id}/products", response_model=List[ProductModel])
async def get_user_products(user_id: int, db: Session = Depends(get_db)):
    products = db.query(Producto).filter(Producto.vendedor_id == user_id).all()
    product_list = [
        {
            "nombre_producto": product.nombre_producto,
            "marca": product.marca,
            "modelo": product.modelo,
            "precio": product.precio,
            "descripcion": product.descripcion,
            "localizacion": product.localizacion,
            "categoria": product.categoria.nombre
        }
        for product in products
    ]
    return product_list

@app.get("/allproducts")
async def list_products(user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    products = db.query(Producto).filter(Producto.vendedor_id != user.usuario_id).all()
    return products

@app.get("/products/category/{category_name}")
async def get_products_by_category(category_name: str, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    products = db.query(Producto).join(Categoria).filter(
        Categoria.nombre == category_name,
        Producto.vendedor_id != user.usuario_id  # Excluir productos del propio usuario
    ).all()

    return products

@app.get("/products/{product_id}")
async def get_product(product_id: int, db: Session = Depends(get_db)):
    return find_product_by_id(product_id, db)

@app.put("/products/{product_id}")
async def update_product(product_id: int, product: ProductModel, db: Session = Depends(get_db)):
    return update_product(product_id, product, db) 

@app.delete("/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    return delete_user_by_id(product_id, db)

@app.get("/products/search", response_model=List[ProductModel])
async def search_products_with_filters(query: ProductQuery = Depends(), db: Session = Depends(get_db)):
    return search_products(query, db)

@app.get("/categories", response_model=List[dict])
async def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Categoria).all()
    return [{"categoria_id": category.categoria_id, "nombre": category.nombre} for category in categories]


# Messages
@app.post("/messages/", response_model=Message)
async def send_message(message: Message, db: Session = Depends(get_db)):
    db_message = Mensaje(
        producto_id=message.producto_id,
        id_usuario_envia=message.id_usuario_envia,
        id_usuario_recibe=message.id_usuario_recibe,
        contenido=message.contenido,
        fecha_envio=message.fecha_envio,
        leido=message.leido
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

@app.get("/messages/received/{user_id}", response_model=List[Message])
async def list_received_messages(user_id: int, db: Session = Depends(get_db)):
    messages = db.query(Mensaje).filter(Mensaje.id_usuario_recibe == user_id).all()
    return messages

@app.get("/messages/sent/{user_id}", response_model=List[Message])
async def list_sent_messages(user_id: int, db: Session = Depends(get_db)):
    messages = db.query(Mensaje).filter(Mensaje.id_usuario_envia == user_id).all()
    return messages

@app.get("/messages/product/{product_id}", response_model=List[Message])
async def list_messages_by_product(product_id: int, db: Session = Depends(get_db)):
    messages = db.query(Mensaje).filter(Mensaje.producto_id == product_id).all()
    return messages

@app.get("/messages/chat/{product_id}/{user1_id}/{user2_id}", response_model=List[Message])
async def list_chat_messages(product_id: int, user1_id: int, user2_id: int, db: Session = Depends(get_db)):
    messages = db.query(Mensaje).filter(
        Mensaje.producto_id == product_id,
        ((Mensaje.id_usuario_envia == user1_id) & (Mensaje.id_usuario_recibe == user2_id)) |
        ((Mensaje.id_usuario_envia == user2_id) & (Mensaje.id_usuario_recibe == user1_id))
    ).all()
    return messages


@app.get("/messages/user/{user_id}", response_model=List[Message])
async def list_user_messages(user_id: int, db: Session = Depends(get_db)):
    messages = db.query(Mensaje).filter(
        (Mensaje.id_usuario_envia == user_id) | (Mensaje.id_usuario_recibe == user_id)
    ).all()
    return messages





@app.get("/users/{user_id}/chats")
async def get_user_chats(user_id: int, db: Session = Depends(get_db)):
    chats = db.query(Mensaje).options(joinedload(Mensaje.producto)).filter(
        (Mensaje.id_usuario_envia == user_id) | (Mensaje.id_usuario_recibe == user_id)
    ).all()
    return chats


# Reviews
@app.post("/reviews/", response_model=Review)
async def leave_review(review: Review, db: Session = Depends(get_db)):
    db_review = Valoracion(
        de_usuario_id=review.de_usuario_id,
        para_usuario_id=review.para_usuario_id,
        puntuacion=review.puntuacion,
        comentario=review.comentario,
        fecha_valoracion=review.fecha_valoracion
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

@app.get("/reviews/{user_id}", response_model=List[Review])
async def get_reviews(user_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Valoracion).filter(Valoracion.para_usuario_id == user_id).all()
    return reviews

# Transactions
@app.post("/transactions/")
async def create_transaction(transaction: TransactionModel, db: Session = Depends(get_db)):
    db_transaction = Transaccion(
        comprador_id=transaction.comprador_id,
        vendedor_id=transaction.vendedor_id,
        producto_id=transaction.producto_id,
        fecha_transaccion=transaction.fecha_transaccion,
        monto=transaction.monto,
        stripe_payment_id=transaction.stripe_payment_id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@app.get("/transactions/", response_model=List[TransactionModel])
async def list_transactions(db: Session = Depends(get_db)):
    transactions = db.query(Transaccion).all()
    return transactions

@app.get("/transactions/{transaction_id}", response_model=TransactionModel)
async def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(Transaccion).filter(Transaccion.transaccion_id == transaction_id).first()
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

# Shipments
@app.post("/shipments/", response_model=Shipment)
async def register_shipment(shipment: Shipment, db: Session = Depends(get_db)):
    db_shipment = Envio(
        transaccion_id=shipment.transaccion_id,
        estado_envio=shipment.estado_envio,
        fecha_envio=shipment.fecha_envio
    )
    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

@app.put("/shipments/{shipment_id}", response_model=Shipment)
async def update_shipment_status(shipment_id: int, shipment: Shipment, db: Session = Depends(get_db)):
    db_shipment = db.query(Envio).filter(Envio.envio_id == shipment_id).first()
    if db_shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    db_shipment.estado_envio = shipment.estado_envio
    db_shipment.fecha_envio = shipment.fecha_envio
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

@app.get("/shipments/{shipment_id}", response_model=Shipment)
async def get_shipment_details(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.query(Envio).filter(Envio.envio_id == shipment_id).first()
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment

# Start the Uvicorn server to run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
