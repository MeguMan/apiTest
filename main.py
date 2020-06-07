import uvicorn
import secrets
from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
import os

DATABASE = {
    'NAME': os.environ.get('DB_NAME', 'SeriesDB'),
    'HOST': os.environ.get('DB_HOST', 'localhost'),
    'PORT': int(os.environ.get('DB_PORT', '27017')),
    'COLLECTION': 'secrets'
}


class Item(BaseModel):
    secret: str
    code_phrase: str


client = MongoClient(host=DATABASE['HOST'], port=DATABASE['PORT'])
db = client[DATABASE['NAME']]
collection = db[DATABASE['COLLECTION']]

app = FastAPI()

file = open('key.key', 'rb')
crypt_key = file.read()
file.close()
f = Fernet(crypt_key)


@app.post("/generate", status_code=201)
async def create_item(item: Item):
    secret_key = secrets.token_urlsafe(64)

    secret = item.secret.encode()
    code_phrase = item.code_phrase.encode()

    collection.insert_one({
        'secret_key': secret_key,
        'secret': f.encrypt(secret),
        'code_phrase': f.encrypt(code_phrase)
    })

    return {
        "secret_key": secret_key
    }


@app.get("/secrets/{secret_key}")
async def read_secret(secret_key, code_phrase: str):
    secret = collection.find_one({'secret_key': secret_key})
    if secret:
        for key in secret:
            if key == 'secret' or key == 'code_phrase':
                secret[key] = f.decrypt(secret[key]).decode()

        if code_phrase == secret['code_phrase']:
            collection.delete_one({'secret_key': secret_key})
            return secret['secret']
        raise HTTPException(status_code=403, detail="Wrong code_phrase")
    raise HTTPException(status_code=404, detail='Wrong secret key')


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
