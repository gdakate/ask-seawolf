"""Authentication utilities: JWT tokens and password hashing."""
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)
settings = get_settings()

SBU_DOMAINS = {"stonybrook.edu", "cs.stonybrook.edu", "ams.stonybrook.edu"}


def validate_sbu_email(email: str) -> None:
    """Raise 400 if email is not from an allowed SBU domain."""
    domain = email.lower().split("@")[-1] if "@" in email else ""
    if domain not in SBU_DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only @stonybrook.edu email addresses are allowed.",
        )


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Dependency to extract and validate admin user from JWT."""
    payload = decode_token(credentials.credentials)
    email = payload.get("sub")
    if not email or payload.get("type") == "public":
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"email": email, "role": payload.get("role", "admin")}


async def get_current_public_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Dependency to extract and validate public user from JWT."""
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id or payload.get("type") != "public":
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"id": user_id, "email": payload.get("email", "")}
