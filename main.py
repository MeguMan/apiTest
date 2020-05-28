import uvicorn
import redis
import secrets
import pickle
from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException

r = redis.Redis(host='localhost', port=6379, db=1)
app = FastAPI()

file = open('key.key', 'rb')
crypt_key = file.read()
file.close()
f = Fernet(crypt_key)


@app.get("/generate")
async def read_data(secret: str, code_phrase: str):
    secret_key = secrets.token_urlsafe(64)

    secret = secret.encode()
    code_phrase = code_phrase.encode()

    r.set(secret_key, pickle.dumps({
        'secret': f.encrypt(secret),
        'code_phrase': f.encrypt(code_phrase)
    }))

    return {
        "secret_key": secret_key
    }


@app.get("/secrets/{secret_key}")
async def read_secret(secret_key, code_phrase: str):
    if r.get(secret_key):
        secret = pickle.loads(r.get(secret_key))

        for key in secret:
            secret[key] = f.decrypt(secret[key]).decode()

        if code_phrase == secret['code_phrase']:
            r.delete(secret_key)
            return secret
        raise HTTPException(status_code=404, detail="Wrong code_phrase")
    raise HTTPException(status_code=404, detail='Wrong secret key')


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
