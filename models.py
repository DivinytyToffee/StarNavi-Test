from datetime import datetime
from typing import Optional, List

from pydantic.main import BaseModel


class UserBase(BaseModel):
    username: str
    age: Optional[int] = None
    email: Optional[str] = None
    disabled: Optional[bool] = False
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


class Like(BaseModel):
    username: str
    date: datetime


class Post(BaseModel):
    title: str
    text: str


class PostInDB(Post):
    creator: str
    create_date: datetime
    likes: Optional[List[Like]] = None


class PostOut(PostInDB):
    id: str
