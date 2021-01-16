from datetime import timedelta, datetime
from typing import List, Optional

from bson import ObjectId
from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm

from helpers import get_password_hash, authenticate_user, create_access_token, \
    get_current_active_user, check_like
from models import UserBase, UserIn, UserOut, UserInDB, Token, Post, PostInDB, \
    PostOut, Like
from settings import db, ACCESS_TOKEN_EXPIRE_MINUTES

app = FastAPI()


@app.post("/api/token", response_model=Token)
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


@app.post("/api/user")
async def create_user(user: UserIn):
    try:
        users = db.users
        check_user = users.find_one({'username': user.username})
        if check_user is None:
            dict_in = user.dict()
            dict_in.update({'hashed_password': get_password_hash(user.password)})

            user_id = users.insert_one(UserInDB(**dict_in).dict()).inserted_id
            if user_id:
                return {'user_id': str(user_id)}
            else:
                return HTTPException(423, 'Can\'t create user')
        else:
            return HTTPException(404, 'User already exist')
    except Exception as ex:
        return HTTPException(404, str(ex))


@app.get("/api/user", response_model=UserOut)
async def get_user_data(
        current_user: UserBase = Depends(get_current_active_user)
):
    try:
        username = current_user.username
        user = db.users.find_one({'username': username})
        if user is not None:
            return user
        else:
            return HTTPException(404, 'User is not exist')
    except Exception as ex:
        return HTTPException(404, ex)


@app.post("/api/post")
async def create_posts(
        post: Post,
        current_user: UserBase = Depends(get_current_active_user)
):
    try:
        post_db = PostInDB(
            **post.dict(),
            creator=current_user.username,
            create_date=datetime.now()
        )
        post_id = db.posts.insert_one(post_db.dict()).inserted_id

        if post_id:
            return {'user_id': str(post_id)}
        else:
            return HTTPException(423, 'Can\'t create post')

    except Exception as ex:
        return HTTPException(404, ex)


@app.get("/api/post", response_model=List[PostOut])
async def get_post_list(count: int = 10, page: int = 1, username: Optional[str] = None):
    sort = None
    if username:
        sort = {'creator': username}

    list_out = db.posts.find(sort).skip(count*(page-1)).limit(count)
    return [PostOut(**x, id=str(x.get('_id'))) for x in list_out]


@app.get("/api/post/{post_id}", response_model=PostOut)
async def get_post(post_id: str):
    try:
        post = db.posts.find_one({'_id': ObjectId(post_id)})
        if post is not None:
            return PostOut(**post, id=str(post.get('_id')))
        else:
            return HTTPException(404, 'Post is not exist')

    except Exception as ex:
        return HTTPException(404, ex)


@app.put('/api/post/like/{post_id}')
async def like_post(
        post_id: str,
        current_user: UserBase = Depends(get_current_active_user)
):
    try:
        post = db.posts.find_one({'_id': ObjectId(post_id)})
        if post is not None:
            likes = post.get('likes') if post.get('likes') else []

            if check_like(current_user.username, likes):
                return HTTPException(404, 'post already likes')

            likes.append(
                Like(username=current_user.username, date=datetime.now()).dict()
            )
            result = db.posts.update_one(
                {'_id': ObjectId(post_id)},
                {'$set': {'likes': likes}}
            )

            if result:
                return Response('', 204)
            else:
                return HTTPException(422, 'can\'t insert')
        else:
            return HTTPException(404, 'Post is not exist')

    except Exception as ex:
        return HTTPException(404, ex)


@app.put('/api/post/unlike/{post_id}')
async def unlike_post(
        post_id: str,
        current_user: UserBase = Depends(get_current_active_user)
):
    try:
        post = db.posts.find_one({'_id': ObjectId(post_id)})
        if post is not None:
            result = db.posts.update_one(
                {'_id': ObjectId(post_id)},
                {"$pull": {'likes': {"username": current_user.username}}},
                False,
                True
            )

            if result:
                return Response('', 204)
            else:
                return HTTPException(422, 'can\'t insert')
        else:
            return HTTPException(404, 'Post is not exist')

    except Exception as ex:
        return HTTPException(404, ex)


@app.get('/api/analitics')
async def get_likes_count(date_from: datetime, date_to: datetime):
    pass
