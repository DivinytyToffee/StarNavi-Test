from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from pymongo import MongoClient

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
client = MongoClient()
db = client.test_database

SECRET_KEY = "aa5dfa23a654b55c04e55980ac2af78fce91148aad6e7c6615580f8e311acb4a"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class UserBase(BaseModel):
    username: str
    age: Optional[int] = None
    email: Optional[str] = None
    disabled: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserIn(UserBase):
    password: str


class UserOut(UserBase):
    pass


class UserInDB(UserBase):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    user = db.users.find_one({'username': username})
    user.pop('_id')

    if user is not None:
        return UserInDB(**user)
    else:
        return HTTPException(404, 'User is not exist')


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: UserBase = Depends(get_current_user)
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends()
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/user", response_model=UserIn)
async def create_user(user: UserIn):
    try:
        users = db.users
        check_user = users.find_one({'username': user.username})
        if check_user is None:

            user_id = users.insert_one(
                UserInDB(**user.dict(),
                         hashed_password=get_password_hash(user.password))
            ).inserted_id
            if user_id:
                return {'user_id': str(user_id)}
            else:
                return HTTPException(423, 'Can\'t create user')
        else:
            return HTTPException(404, 'User already exist')
    except Exception as ex:
        return HTTPException(404, ex)


@app.get("/user", response_model=UserOut)
async def get_user(current_user: UserBase = Depends(get_current_active_user)):
    try:
        username = current_user.username
        user = db.users.find_one({'username': username})
        user.pop('_id')
        if user is not None:
            return user
        else:
            return HTTPException(404, 'User is not exist')
    except Exception as ex:
        return HTTPException(404, ex)
