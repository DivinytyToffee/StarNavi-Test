from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from pymongo import MongoClient

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
client = MongoClient()
db = client.test_database

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}


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


@app.post("/user", response_model=UserBase)
async def create_user(user: UserBase):
    try:
        users = db.users
        check_user = users.find_one({'username': user.username})
        if check_user is None:
            user_id = users.insert_one(user.dict()).inserted_id
            if user_id:
                return {'user_id': str(user_id)}
            else:
                return HTTPException(423, 'Can\'t create user')
        else:
            return HTTPException(404, 'User already exist')
    except Exception as ex:
        return HTTPException(404, ex)


@app.get("/user/{username}", response_model=UserOut)
async def get_user(username: str):
    try:
        user = db.users.find_one({'username': username})
        user.pop('_id')
        if user is not None:
            return user
        else:
            return HTTPException(404, 'User is not exist')
    except Exception as ex:
        return HTTPException(404, ex)
