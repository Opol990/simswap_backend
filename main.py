
from fastapi import FastAPI, Path,HTTPException, Depends,Request,status
from pydantic import BaseModel, ValidationError
from typing import List,Optional
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt 
from datetime import datetime, timedelta
from utils.models import UserModel, LoginRequest, RegisterUserRequest, FindUserRequest, UpdateUserRequest, ProductModel, ProductQuery, AdvertisementModel
from utils.sql_scripts import *
from utils.sql_connection import Base, engine
from utils.tools import create_access_token
from dotenv import load_dotenv
import os
from sqlalchemy.orm import Session

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


#Middleware
@app.middleware("http")
async def verify_jwt(request: Request, call_next):
    bypass_routes = ["/docs", "/openapi.json", "/redoc", "/login", "/token", "/users/signup"] #Rutas en las que no actua el middleware
    
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
        if 'email' not in payload or 'password' not in payload:
            raise HTTPException(status_code=400, detail="Invalid token data")
        request.state.user = payload  # Store the entire payload if needed, or just the email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token or expired token")

    response = await call_next(request)
    return response





# # Users
@app.post("/users/signup")
async def register_user(user: RegisterUserRequest,  db: Session = Depends(get_db)):
    user_info = register_new_user(user_request=user, db=db)
    return user_info

@app.post("/login")
async def login_for_access_token(item:LoginRequest, db: Session = Depends(get_db)):
    access_token = user_login(email=item.email, pwd=item.password, db=db)
    return access_token

@app.get("/users/{user_id}")
async def find_user_by_id(user_id:int, db: Session = Depends(get_db)):
    if user_id:    
        return get_user_by_id(user_id, db)

@app.put("/users/{user_id}")
async def update_user_by_id(user_id:int, user: UpdateUserRequest, db: Session = Depends(get_db) ):
    return update_user(user_id, user, db)

@app.delete("/users/{user_id}")
async def delete_user_by_id(user_id:int, db: Session = Depends(get_db)):
    message_deleted = delete_user(user_id, db)
    return {"message_deleted": message_deleted}




# Products
@app.post("/products/")
async def add_product(product: ProductModel, db: Session = Depends(get_db)):
    product = create_product(product, db)
    return product  

@app.get("/products/")
async def list_products(db: Session = Depends(get_db)):
    return  find_all_products(db)

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





# Advertisements
@app.post("/advertisements/")
async def create_anuncio(ad: AdvertisementModel, db: Session = Depends(get_db)):
    return add_anuncio(ad, db)

@app.get("/advertisements/")
async def list_anuncios(db: Session = Depends(get_db)):
    return get_all_anuncios(db)

@app.get("/advertisements/{ad_id}")
async def get_anuncios(ad_id: int, db: Session = Depends(get_db)):
    return get_anuncio_by_id(ad_id, db)

@app.put("/advertisements/{ad_id}")
async def update_advertisement(ad_id: int, ad: AdvertisementModel, db: Session = Depends(get_db)):
    return update_anuncio(ad_id, ad, db) # Mock implementation

@app.delete("/advertisements/{ad_id}")
async def delete_advertisement(ad_id: int, db: Session = Depends(get_db)):
    return delete_anuncio_by_id(ad_id, db)





# # Messages
# @app.post("/messages/", response_model=Message)
# async def send_message(message: Message):
#     return message  # Mock implementation

# @app.get("/messages/received/{user_id}", response_model=List[Message])
# async def list_received_messages(user_id: int):
#     return []  # Mock implementation

# @app.get("/messages/sent/{user_id}", response_model=List[Message])
# async def list_sent_messages(user_id: int):
#     return []  # Mock implementation

# # Reviews
# @app.post("/reviews/", response_model=Review)
# async def leave_review(review: Review):
#     return review  # Mock implementation

# @app.get("/reviews/{user_id}", response_model=List[Review])
# async def get_reviews(user_id: int):
#     return []  # Mock implementation

# # Transactions
# @app.post("/transactions/", response_model=Transaction)
# async def create_transaction(transaction: Transaction):
#     return transaction  # Mock implementation

# @app.get("/transactions/", response_model=List[Transaction])
# async def list_transactions():
#     return []  # Mock implementation

# @app.get("/transactions/{transaction_id}", response_model=Transaction)
# async def get_transaction(transaction_id: int):
#     return {}  # Mock implementation

# # Shipments
# @app.post("/shipments/", response_model=Shipment)
# async def register_shipment(shipment: Shipment):
#     return shipment  # Mock implementation

# @app.put("/shipments/{shipment_id}", response_model=Shipment)
# async def update_shipment_status(shipment_id: int, shipment: Shipment):
#     return shipment  # Mock implementation

# @app.get("/shipments/{shipment_id}", response_model=Shipment)
# async def get_shipment_details(shipment_id: int):
#     return {}  # Mock implementation

# Start the Uvicorn server to run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)