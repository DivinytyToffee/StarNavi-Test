from datetime import timedelta, datetime
from functools import wraps
from typing import Optional

from fastapi import HTTPException, Depends
from jose import jwt, JWTError
from starlette import status

from models import UserInDB, TokenData, UserBase
from settings import pwd_context, db, SECRET_KEY, ALGORITHM, oauth2_scheme


def verify_password(plain_password, hashed_password):
    """
    Function to verify if a received password matches the hash stored.

    :param plain_password:
    :param hashed_password:
    :return:
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Function to hash a password coming from the user.

    :param password:
    :return:
    """
    return pwd_context.hash(password)


def get_user(username: str):
    """
    Function to return user for username from database.

    :param username:
    :return:
    """
    user = db.users.find_one({'username': username})

    if user is not None:
        return UserInDB(**user)
    else:
        return HTTPException(404, 'User is not exist')


def authenticate_user(username: str, password: str):
    """
    Function to authenticate and return a user.

    :param username:
    :param password:
    :return:
    """
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Function to generate a new access token.

    :param data:
    :param expires_delta:
    :return:
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Function to decode JWT and return user.

    :param token:
    :return:
    """
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
    """
    Function to check if the user is active.

    :param current_user:
    :return:
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    log_activity_user(current_user.username)
    return current_user


async def get_current_admin_user(
        current_user: UserBase = Depends(get_current_user)
):
    """
    Function to check if the user is admin.

    :param current_user:
    :return:
    """
    if get_current_active_user(current_user):
        log_activity_user(current_user.username)
        if current_user.admin:
            return current_user

    raise HTTPException(status_code=400, detail="No access")


def check_like(username, likes):
    """
    The function checks if the user has marked the post as liked.

    :param username:
    :param likes:
    :return:
    """
    if likes:
        for x in likes:
            if x.get('username') == username:
                return True
    return False


def log_login_user(username):
    """
    Function to log last user login.

    :param username:
    :return:
    """
    db.statistic.update_one(
        {'username': username},
        {'$set': {'log-in-date': datetime.now()}},
        upsert=True
    )


def log_activity_user(username):
    """
    Function to log last user server access.

    :param username:
    :return:
    """
    db.statistic.update_one(
        {'username': username},
        {'$set': {'last-server-access': datetime.now()}},
        upsert=True
    )


def security_decorator(func):
    """
    Decorator to wrap endpoint for create try/except logic.

    :param func:
    :return:
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as ex:
            return HTTPException(500, str(ex))

    return wrapper
