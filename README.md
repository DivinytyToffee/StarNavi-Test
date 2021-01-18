# RUN Server:

install requirements `pip install -r requirements.txt`

run server `uvicorn main:app --reload`

List of requests on `localhost:8000/docs`

# BOT:

run bot for demonstration as `python bot/bot.py config.json`.

you may add `--deleted` flag to delete  random created users and posts.

## config file

### users block

`random_user_count` - int, a value that determines the number of randomly created users

`users_list` - list, containes objects with username and password, _optional_

### posts block

`max_posts_per_user` - int, a value that determines the max number of randomly created posts

`min_posts_per_user` - int, a value that determines the min number of randomly created posts, _optional_

max_likes_per_user - int, the value that determines the max number of posts that will be marked as liked

max_likes_per_user - int, the value that determines the min number of posts that will be marked as liked, _optional_

