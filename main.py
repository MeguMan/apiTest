import uvicorn
import secrets
from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.avito_test
collection = db.secrets

app = FastAPI()

file = open('key.key', 'rb')
crypt_key = file.read()
file.close()
f = Fernet(crypt_key)


@app.get("/generate", status_code=201)
async def read_data(secret: str, code_phrase: str):
    secret_key = secrets.token_urlsafe(64)

    secret = secret.encode()
    code_phrase = code_phrase.encode()

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
