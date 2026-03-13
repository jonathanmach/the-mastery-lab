import base64
import time

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fastapi import APIRouter
from jose import jwt
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth")

# Generate RSA key pair at module load (dev-only, in-memory)
_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_public_key = _private_key.public_key()

_KID = "dev-key-1"

# PEM-encoded private key for jose JWT signing
_private_pem = _private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

# Extract RSA public numbers for JWKS endpoint
_pub_numbers = _public_key.public_numbers()


def _int_to_base64url(n: int) -> str:
    byte_length = (n.bit_length() + 7) // 8
    raw = n.to_bytes(byte_length, byteorder="big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


_JWKS = {
    "keys": [
        {
            "kty": "RSA",
            "alg": "RS256",
            "use": "sig",
            "kid": _KID,
            "n": _int_to_base64url(_pub_numbers.n),
            "e": _int_to_base64url(_pub_numbers.e),
        }
    ]
}


class TokenRequest(BaseModel):
    user_id: str


@router.post("/token")
def create_token(req: TokenRequest):
    now = int(time.time())
    claims = {
        "sub": req.user_id,
        "aud": "powersync-dev",
        "iat": now,
        "exp": now + 55 * 60,  # 55 minutes (PowerSync rejects >= 60 min)
    }
    token = jwt.encode(claims, _private_pem, algorithm="RS256", headers={"kid": _KID})
    return {
        "token": token,
        "powersync_url": "http://localhost:8180",
    }


@router.get("/keys")
def get_keys():
    return _JWKS
