from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
from datetime import timedelta
from hashlib import sha256

import db
import mongo
from config import client_db, ACCESS_TOKEN_EXPIRE_MINUTES, Chat, User, Wall, Message
from jwt_auth import pwd_context, create_access_token, get_current_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init()
    yield


app = FastAPI(lifespan=lifespan)


# Маршрут для получения токена
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    password_check = False
    response = await db.get_user(form_data.username)

    if "status" not in response.keys():
        password = response["hashed_password"].strip()
        if sha256(form_data.password.encode()).hexdigest() == password:
            password_check = True

    if password_check:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


# PUT /users/{login}/send_message/{target_login} - Отправка сообщения
@app.put("/users/{login}/send_message/{target_login}", response_model=Chat)
async def send_message(
    login: str,
    target_login: str,
    body: str,
    current_user: str = Depends(get_current_client),
):
    # if login in client_db.keys() and target_login in client_db.keys():
    if "status" not in await db.get_user(login) and "status" not in await db.get_user(
        target_login
    ):
        # Есть ли у пользователей чат
        response = await db.get_chats(login, target_login)

        if "status" not in response:
            chat_id = response["chat_id"]

        else:
            # Создаём новый чат
            await db.add_new_chat(login, target_login)
            response = await db.get_chats(login, target_login)
            chat_id = response["chat_id"]

        # Создаём новое сообщение
        await db.add_message(chat_id, login, body)

        # Возвращаем чат
        response = await db.get_chats(login, target_login)
        messages = response["messages"]

        return Chat(
            messages=[Message.model_validate(i) for i in messages],
            login1=response["users"][0],
            login2=response["users"][1],
        )

    raise HTTPException(status_code=404, detail="User not found")


# GET /users/{user_id}/wall - Получить список сообщений (требует аутентификации)
@app.get("/users/{login}/chat/{target_login}", response_model=Chat)
async def get_chat(
    login: str, target_login: str, current_user: str = Depends(get_current_client)
):
    response = await db.get_user(login)

    if "status" not in response.keys():
        response = await db.get_chats(login, target_login)

        if "status" not in response.keys():
            messages = response["messages"]

            return Chat(
                messages=[Message.model_validate(i) for i in messages],
                login1=response["users"][0],
                login2=response["users"][1],
            )

        raise HTTPException(status_code=404, detail="Chat not found")

    raise HTTPException(status_code=404, detail="User not found")


# GET /users/{user_id}/wall - Получить стену пользователя (требует аутентификации)
@app.get("/users/{login}/wall", response_model=Wall)
async def get_wall(login: str, current_user: str = Depends(get_current_client)):
    response = await db.get_user(login)

    if "status" not in response.keys():
        response = await db.get_wall(login)

        if "status" not in response.keys():
            return Wall(posts=[response["posts"]])

        raise HTTPException(status_code=404, detail="Wall not found")

    raise HTTPException(status_code=404, detail="User not found")


# POST /users/{login}/create_post - Создать нового поста на стене
@app.post("/users/{login}/create_post", response_model=Wall)
async def create_post(
    login: str, post_txt: str, current_user: str = Depends(get_current_client)
):
    response = await db.get_user(login)

    if "status" not in response.keys():
        response = await db.add_new_post(post_txt, login)

        if "status" not in response:
            return Wall(posts=[post_txt])

    raise HTTPException(status_code=404, detail="User not found")


# GET /users/{user_id} - Получить пользователя по имени и фамилии (требует аутентификации)
@app.get("/users/{name}/{surname}", response_model=User)
async def get_user_by_name(
    name: str, surname: str, current_user: str = Depends(get_current_client)
):
    response = await db.get_user_by_name(name, surname)

    if "status" not in response.keys():
        return response

    raise HTTPException(status_code=404, detail=response)


# GET /users/{user_id} - Получить пользователя по логину (требует аутентификации)
@app.get("/users/{login}", response_model=User)
async def get_user(login: str, current_user: str = Depends(get_current_client)):
    response = await db.get_user(login)

    if "status" not in response.keys():
        return User.model_validate(response)

    raise HTTPException(status_code=404, detail=response)


# POST /users - Создать нового пользователя
@app.post("/users", response_model=User)
async def create_user(user: User):
    if user.login in client_db.keys():
        raise HTTPException(status_code=404, detail="User already exist")

    else:
        # Предполагается, что при регистрации пользователь передаст не хэшированный пароль
        # (По правильному, конечно, надо сразу на стороне клиента пароль хэшировать)
        user.hashed_password = sha256(user.hashed_password.encode()).hexdigest()
        await db.add_new_user(user.login, user.hashed_password, user.name, user.surname)

    return user


@app.get("/debug_select")
async def get_all_tables():
    mongo.find_document_by_user_name(user_name="admin")
    await db.select_all_users()
    await db.select_all_chats()
    await db.select_all_messages()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)