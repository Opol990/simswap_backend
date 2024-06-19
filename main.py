
from fastapi import BackgroundTasks, FastAPI, HTTPException, Depends,Request
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt 
from datetime import datetime, timedelta
import stripe
from utils.models import Message,  TransactionModel, UpdateProduct, LoginRequest, RegisterUserRequest,  UpdateUserRequest, ProductModel
from utils.sql_scripts import *
from utils.sql_connection import Base, engine
from utils.tools import  send_email
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
    allow_methods=origins,
    allow_headers=origins,
)

bypass_routes = ["/docs", "/openapi.json", "/redoc", "/users/login", "/users/signup", ]


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


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
async def update_user_endpoint(user_data: UpdateUserRequest, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    updated_user = update_user_info(user.usuario_id, user_data, db)
    return updated_user

# @app.delete("/users/{user_id}")
# async def delete_user_by_id(user_id:int, db: Session = Depends(get_db)):
#     message_deleted = delete_user(user_id, db)
#     return {"message_deleted": message_deleted}


@app.get("/users/{user_id}")
async def find_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Products
@app.post("/products/")
async def add_product(product: ProductModel, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    product = create_product(product, user, db)
    return product  

@app.get("/users/{user_id}/products", response_model=List[ProductResponse])
async def get_user_products_endpoint(user_id: int, db: Session = Depends(get_db)):
    return get_user_products(user_id, db)


@app.get("/allproducts")
async def list_products(user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    products = db.query(Producto).filter(Producto.vendedor_id != user.usuario_id, Producto.disponibilidad == 'disponible').all()
    return products

@app.get("/products/category/{category_name}")
async def get_products_by_category_endpoint(category_name: str, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_products_by_category(category_name, user.usuario_id, db)


@app.get("/products/{product_id}")
async def get_product(product_id: int, db: Session = Depends(get_db)):
    return find_product_by_id(product_id, db)

@app.put("/products/{product_id}", response_model=ProductModel)
@app.put("/products/{product_id}", response_model=ProductModel)
async def update_user_product_endpoint(product_id: int, product: UpdateProduct, db: Session = Depends(get_db)):
    return update_product(product_id, product, db)


@app.delete("/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    return delete_product_by_id(product_id, db)

# @app.get("/products/search", response_model=List[ProductModel])
# async def search_products_with_filters(query: ProductQuery = Depends(), db: Session = Depends(get_db)):
#     return search_products(query, db)

@app.get("/products/vendedor/{producto_id}")
async def get_vendedor_id_and_disponibilidad(producto_id: int, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.producto_id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"vendedor_id": producto.vendedor_id, "disponibilidad": producto.disponibilidad}




@app.get("/categories", response_model=List[dict])
async def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Categoria).all()
    return [{"categoria_id": category.categoria_id, "nombre": category.nombre} for category in categories]

@app.post("/create-checkout-session")
async def create_checkout_session(data: TransactionModel, db: Session = Depends(get_db)):
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': data.nombre_producto,
                    },
                    'unit_amount': int(data.monto * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url="http://localhost:3000/checkout-success",
            cancel_url="http://localhost:3000/cancel",
        )

        data.stripe_payment_id = checkout_session.id

        return {
            "url": checkout_session.url,
            "transaction": data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/purchase_product")
async def purchase_product(
    transaction: TransactionModel, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):

    try:
        db_product = db.query(Producto).filter(Producto.producto_id == transaction.producto_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        db_product.disponibilidad = 'vendido'
        db.commit()

        print("Producto actualizado")

        db_transaction = Transaccion(
            comprador_id=transaction.comprador_id,
            vendedor_id=transaction.vendedor_id,
            producto_id=transaction.producto_id,
            fecha_transaccion=datetime.utcnow(),
            monto=transaction.monto,
            stripe_payment_id=transaction.stripe_payment_id
        )
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)

        comprador = db.query(Usuario).filter(Usuario.usuario_id == transaction.comprador_id).first()
        vendedor = db.query(Usuario).filter(Usuario.usuario_id == transaction.vendedor_id).first()

        print("Comprador y vendedor encontrados")

        background_tasks.add_task(
            send_email,
            "Producto Vendido",
            vendedor.email,
            f"Tu producto {db_product.nombre_producto} ha sido vendido."
        )

        background_tasks.add_task(
            send_email,
            "Compra Exitosa",
            comprador.email,
            f"Has comprado el producto {db_product.nombre_producto}."
        )


        # Enviar el mensaje a todos los usuarios que tienen un chat sobre el producto
        chats = db.query(Mensaje).filter(Mensaje.producto_id == transaction.producto_id).all()
        user_ids = set()
        for chat in chats:
            if chat.id_usuario_envia != transaction.comprador_id:
                user_ids.add(chat.id_usuario_envia)
            if chat.id_usuario_recibe != transaction.comprador_id:
                user_ids.add(chat.id_usuario_recibe)

        for user_id in user_ids:
            mensaje = Mensaje(
                producto_id=transaction.producto_id,
                id_usuario_envia=transaction.comprador_id,
                id_usuario_recibe=user_id,
                contenido='El producto ha sido comprado y ya no está disponible.',
                fecha_envio=datetime.utcnow(),
                leido=False
            )
            db.add(mensaje)
            db.commit()

        print("Chats Actualizados")

        return db_transaction

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))




# Messages
@app.post("/messages/", response_model=Message)
async def send_message(message: Message, db: Session = Depends(get_db)):
    return create_message(message, db)

# @app.get("/messages/received/{user_id}", response_model=List[Message])
# async def list_received_messages(user_id: int, db: Session = Depends(get_db)):
#     messages = db.query(Mensaje).filter(Mensaje.id_usuario_recibe == user_id).all()
#     return messages

# @app.get("/messages/sent/{user_id}", response_model=List[Message])
# async def list_sent_messages(user_id: int, db: Session = Depends(get_db)):
#     messages = db.query(Mensaje).filter(Mensaje.id_usuario_envia == user_id).all()
#     return messages

# @app.get("/messages/product/{product_id}", response_model=List[Message])
# async def list_messages_by_product(product_id: int, db: Session = Depends(get_db)):
#     messages = db.query(Mensaje).filter(Mensaje.producto_id == product_id).all()
#     return messages

@app.get("/messages/chat/{product_id}/{user1_id}/{user2_id}", response_model=List[Message])
async def list_chat_messages(product_id: int, user1_id: int, user2_id: int, db: Session = Depends(get_db)):
    return get_chat_messages(product_id, user1_id, user2_id, db)


@app.get("/messages/user/{user_id}")
async def list_user_messages(user_id: int, db: Session = Depends(get_db)):
    return get_user_messages(user_id, db)

# @app.get("/users/{user_id}/chats")
# async def get_user_chats(user_id: int, db: Session = Depends(get_db)):
#     chats = db.query(Mensaje).options(joinedload(Mensaje.producto)).filter(
#         (Mensaje.id_usuario_envia == user_id) | (Mensaje.id_usuario_recibe == user_id)
#     ).all()
#     return chats

@app.put("/messages/mark-as-read/{product_id}/{user1_id}/{user2_id}")
async def mark_messages_as_read(product_id: int, user1_id: int, user2_id: int, db: Session = Depends(get_db)):
    mark_messages_read(product_id, user1_id, user2_id, db)
    return {"message": "Messages marked as read"}

# Transactions
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



# Start the Uvicorn server to run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
