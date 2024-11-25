import os
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from functools import wraps

# Настройка подключения
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/my_database")
# MONGO_URI = "mongodb://admin:example@mongo:27017/"
print("!", MONGO_URI, "!")
DATABASE_NAME = "my_database"
COLLECTION_NAME = "my_collection"


def mongo_connection(func):
    """Декоратор для подключения к базе данных MongoDB."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]

        try:
            result = func(db, *args, **kwargs)

        finally:
            client.close()

        return result

    return wrapper


@mongo_connection
def create_index(db):
    """Создание индекса по полю user_name."""
    collection = db[COLLECTION_NAME]
    index_name = collection.create_index([("user_name", ASCENDING)], unique=True)
    return f"Индекс создан: {index_name}"


@mongo_connection
def insert_document(db, document):
    """Добавление JSON-документа в коллекцию."""
    collection = db[COLLECTION_NAME]

    try:
        inserted_id = collection.insert_one(document).inserted_id
        return f"Документ добавлен с _id: {inserted_id}"

    except DuplicateKeyError:
        return {
            "status": "Error",
            "message": "Ошибка: Документ с таким user_name уже существует",
        }


@mongo_connection
def find_document_by_user_name(db, user_name):
    """Поиск документа по полю user_name."""
    collection = db[COLLECTION_NAME]
    document = collection.find_one({"user_name": user_name})

    if document:
        print(document)
        return document

    return {"status": "Error", "message": "Документ не найден"}


@mongo_connection
def init(db):
    sample_document = {
        [
            {"user_name": "admin", "posts": ["My first post", "My second post"]},
            {
                "user_name": "admin2",
                "posts": ["My first post too", "My second post too"],
            },
        ]
    }
    insert_document(db, sample_document)


# Пример использования
if __name__ == "__main__":
    # Создание индекса
    print(create_index())

    # Добавление документа
    sample_document = {
        "user_name": "john_doe",
        "email": "john.doe@example.com",
        "age": 30,
    }
    print(insert_document(sample_document))

    # Поиск документа
    print(find_document_by_user_name("john_doe"))