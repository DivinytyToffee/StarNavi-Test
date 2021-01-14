from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pymongo import MongoClient

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
client = MongoClient()
db = client.test_database
SECRET_KEY = "aa5dfa23a654b55c04e55980ac2af78fce91148aad6e7c6615580f8e311acb4a"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30