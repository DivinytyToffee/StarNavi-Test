from datetime import timedelta, datetime
from typing import List, Optional

from bson import ObjectId
from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm

from helpers import get_password_hash, authenticate_user, create_access_token, \
    get_current_active_user, check_like, log_login_user, get_current_admin_user, security_decorator
from models import UserBase, UserIn, UserOut, UserInDB, Token, Post, PostInDB, \
    PostOut, Like
from settings import db, ACCESS_TOKEN_EXPIRE_MINUTES

app = FastAPI()


@app.post("/token", response_model=Token)
@security_decorator
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

    log_login_user(user.username)

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/user")
@security_decorator
async def create_user(user: UserIn):
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


@app.get("/api/user", response_model=UserOut)
@security_decorator
async def get_user_data(
        current_user: UserBase = Depends(get_current_active_user)
):
    username = current_user.username
    user = db.users.find_one({'username': username})
    if user is not None:
        return user
    else:
        return HTTPException(404, 'User is not exist')


@app.get("/api/users", response_model=List[UserOut])
@security_decorator
async def get_user_list(count: int = 10, page: int = 1):
    list_out = db.users.find().skip(count*(page-1)).limit(count)
    return [UserOut(**x) for x in list_out]


@app.post("/api/post")
@security_decorator
async def create_posts(
        post: Post,
        current_user: UserBase = Depends(get_current_active_user)
):
    post_db = PostInDB(
        **post.dict(),
        creator=current_user.username,
        create_date=datetime.now()
    )
    post_id = db.posts.insert_one(post_db.dict()).inserted_id

    if post_id:
        return {'post_id': str(post_id)}
    else:
        return HTTPException(423, 'Can\'t create post')


@app.get("/api/post", response_model=List[PostOut])
@security_decorator
async def get_post_list(count: int = 10, page: int = 1, username: Optional[str] = None):
    sort = None
    if username:
        sort = {'creator': username}

    list_out = db.posts.find(sort).skip(count*(page-1)).limit(count)
    return [PostOut(**x, id=str(x.get('_id'))) for x in list_out]


@app.get("/api/post/{post_id}", response_model=PostOut)
@security_decorator
async def get_post(post_id: str):
    post = db.posts.find_one({'_id': ObjectId(post_id)})
    if post is not None:
        return PostOut(**post, id=str(post.get('_id')))
    else:
        return HTTPException(404, 'Post is not exist')


@app.put('/api/post/like/{post_id}')
@security_decorator
async def like_post(
        post_id: str,
        current_user: UserBase = Depends(get_current_active_user)
):
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


@app.put('/api/post/unlike/{post_id}')
@security_decorator
async def unlike_post(
        post_id: str,
        current_user: UserBase = Depends(get_current_active_user)
):
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


@app.get('/api/analytics/likes')
@security_decorator
async def get_likes_count(
        date_from: datetime, date_to: datetime,
        current_user: UserBase = Depends(get_current_admin_user)
):
    result = db.posts.count_documents({'likes.date': {'$lt': date_to, '$gte': date_from}})
    return {'likes-count': result}


@app.get('/api/analytics/user-activity')
@security_decorator
async def get_user_activity(
        username: str,
        current_user: UserBase = Depends(get_current_admin_user)
):
    result = db.statistic.find_one({'username': username})
    if result:
        result.pop('_id')
    return result


@app.get("/api/analytics/users")
@security_decorator
async def get_user_list(admin_user: UserBase = Depends(get_current_admin_user)):
    result = db.users.count_documents({})
    return {'count-user': result}
