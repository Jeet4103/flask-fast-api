from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

Jwt_secret = '920328a04a1c3222adf3f7f22aa8d07b'
Jwt_algorithm = 'HS256'
AccessTokenExpiresMinutes = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=AccessTokenExpiresMinutes)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, Jwt_secret, algorithm=Jwt_algorithm)

    return encoded_jwt

def decode_token(token):
    try:
        payload = jwt.decode(token, Jwt_secret, algorithms=[Jwt_algorithm])
        return payload

    except ExpiredSignatureError:
        print("Token has expired")
        return None

    except InvalidTokenError:
        print("Invalid token")
        return None
    
