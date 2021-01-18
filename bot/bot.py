import json
import random
import string
import sys


import requests

from bson import ObjectId
from pymongo import MongoClient

HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json'
}
URL = "http://127.0.0.1:8000"
BASE = {}
CLIENT = MongoClient()
DB = CLIENT.test_database


class StopFunction(Exception):
    pass


def break_main(condition: bool, message: str):
    """
    Function to break function.

    :param condition:
    :param message:
    :return:
    """
    if condition:
        print(message)
        raise StopFunction


def read_config(file_name: str):
    """
    Function to read data from config.

    :param file_name:
    :return:
    """
    config_data = None
    try:
        with open(file_name) as json_file:
            config_data = json.loads(json_file.read())

    except FileNotFoundError as fnfe:
        print(fnfe)

    return config_data


def get_token(username: str, password: str):
    """
    Function return token for username and password.

    :param username:
    :param password:
    :return:
    """
    resp = requests.post(
        f"{URL}/token",
        headers=HEADERS,
        data={'username': username, 'password': password}
    )
    if resp.status_code == 200:
        return resp.json().get('access_token')
    return None


def create_user(username: str, password: str, disabled=False, admin=False):
    """
    Function to create user for api.

    :param username:
    :param password:
    :param disabled:
    :param admin:
    :return:
    """
    resp = requests.post(
        f"{URL}/api/user",
        headers=HEADERS,
        json={'username': username,
              'password': password,
              'disabled': disabled,
              'admin': admin
              }
    )
    if resp.status_code == 200:
        return resp.json()
    return None


def create_random_users(count: int):
    """
    Function to create random users.

    :param count:
    :return:
    """

    if isinstance(count, str) and count.isnumeric():
        count = int(count)

    if not isinstance(count, int):
        print('count user is not integer or exist')
        return

    random_users = []
    for x in range(count):
        username = "".join([random.choice(string.ascii_letters)
                            for i in range(8)])
        password = "".join([random.choice(string.printable)
                            for i in range(8)])
        user = create_user(username, password)
        if user and user.get('user_id'):
            print(f'Create user {username}')
            random_users.append({'username': username, 'password': password})

    return random_users


def create_users(users: dict):
    """
    Function to create users from config files.

    :param users:
    :return:
    """
    if users is None:
        return None

    users_list = []
    random_users = create_random_users(users.get('random_user_count'))
    if isinstance(random_users, list):
        users_list.extend(random_users)
        BASE.update({'random-user': random_users})

    if users.get('users_list'):
        for user in users.get('users_list'):
            username = user.get('username')
            password = user.get('password')
            user = create_user(username, username)

            if user and user.get('user_id'):
                users_list.append({'username': username, 'password': password})

            elif user and user.get("detail") == "User already exist":
                users_list.append({'username': username, 'password': password})

    username = 'admin'
    password = 'admin'
    admin = create_user(username, username)

    if admin and admin.get('user_id'):
        users_list.append(
            {'username': username,
             'password': password
             }
        )

    return users_list


def delete_random_users():
    """
    Function to delete create random users.

    :return:
    """
    for x in BASE.get('random-user'):
        DB.users.delete_many({'username': x.get('username')})


def create_post(user: dict):
    """
    Function to create single post.

    :param user:
    :return:
    """
    title = "".join([random.choice(string.ascii_letters) for i in range(8)])
    text = "".join([random.choice(string.ascii_letters) for i in range(110)])
    token = get_token(**user)
    HEADERS.update({'Authorization': f'Bearer {token}'})

    resp = requests.post(
        f"{URL}/api/post",
        headers=HEADERS,
        json={'title': title, 'text': text}
    )
    if resp.status_code == 200:
        print(f'Create post { title } for user: {user.get("username")}')
        return resp.json()
    return None


def create_posts(max_posts: int, min_posts: int):
    """
    Function to create many posts.

    :param max_posts:
    :return:
    """

    if isinstance(max_posts, str) and max_posts.isnumeric():
        max_posts = int(max_posts)

    if isinstance(min_posts, str) and min_posts.isnumeric():
        min_posts = int(min_posts)

    if not isinstance(max_posts, int):
        print('max_posts user is not integer or exist')
        return

    if not isinstance(min_posts, int):
        print('min_posts user is not integer or exist')
        return

    post_list = []

    for user in BASE.get('users'):
        post_count = random.randint(min_posts, max_posts)
        while post_count > 0:
            post = create_post(user)
            if post is not None:
                post_list.append(post.get('post_id'))
            post_count -= 1

    return post_list


def delete_random_posts():
    """
    Function to delete random posts.

    :return:
    """
    for x in BASE.get('posts'):
        DB.posts.delete_many({'_id': ObjectId(x)})


def like_post(user, post_id):
    """
    Function to like random post.

    :param user:
    :param post_id:
    :return:
    """
    token = get_token(**user)
    HEADERS.update({'Authorization': f'Bearer {token}'})

    resp = requests.put(f"{URL}/api/post/like/{post_id}", headers=HEADERS)
    if resp.status_code == 204:
        print(f'Like post { post_id } for user: {user.get("username")}')
        return resp

    return None


def make_likes(max_likes, min_likes):
    """
    Function to send likes post.

    :param max_likes:
    :return:
    """
    if isinstance(max_likes, str) and max_likes.isnumeric():
        max_likes = int(max_likes)

    if not isinstance(max_likes, int):
        print('max_likes user is not integer or exist')
        return

    if isinstance(min_likes, str) and min_likes.isnumeric():
        min_likes = int(min_likes)

    if not isinstance(min_likes, int):
        print('min_likes user is not integer or exist')
        return

    for user in BASE.get('users'):
        likes_count = random.randint(min_likes, max_likes)
        print(likes_count)
        posts = [random.choice(BASE.get('posts')) for x in range(likes_count)]
        for post_id in posts:
            resp = like_post(user, post_id)
            if resp is None:
                print(f'User: {user.get("username")} didn\'t '
                      f'can\'t like post: { post_id }')


def main(*argv):
    try:
        list_elements = argv[0]
        break_main(len(list_elements) < 2, 'Input config file')

        config_data = read_config(list_elements[1])
        break_main(config_data is None, 'Config file is invalid')
        break_main(config_data.get('posts') is None,
                   'Config for posts not create')

        users_list = create_users(config_data.get('users'))
        break_main(len(users_list) == 0, 'Users is not created')
        BASE.update({'users': users_list})

        posts_config = config_data.get('posts')
        max_posts = posts_config.get('max_posts_per_user')
        min_posts = posts_config.get('min_posts_per_user', 0)
        list_posts = create_posts(max_posts, min_posts)
        BASE.update({'posts': list_posts})
        print(len(BASE.get('posts')))

        max_likes = posts_config.get('max_likes_per_user')
        min_likes = posts_config.get('min_likes_per_user', 0)
        make_likes(max_likes, min_likes)

        if len(list_elements) > 2:
            if list_elements[2] == '--deleted':
                print('OK')
                delete_random_users()
                delete_random_posts()

    except StopFunction:
        print('Bot stop')


if __name__ == '__main__':
    main(sys.argv)
