from email.message import EmailMessage
import os
import smtplib
import bcrypt
from jose import jwt 
from datetime import datetime, timedelta



SECRET_KEY = "claveSecreta"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180

    
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def send_email(subject: str, recipient: str, body: str):
    email_message = EmailMessage()
    email_message['Subject'] = subject
    email_message['From'] = os.getenv("EMAIL_SENDER")
    email_message['To'] = recipient
    email_message.set_content(body)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
        smtp.send_message(email_message)
