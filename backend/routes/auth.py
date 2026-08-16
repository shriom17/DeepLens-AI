from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import bcrypt

from backend.database import get_db
from backend.models import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# =========================
# Request Models
# =========================

class RegisterRequest(BaseModel):

    name: str
    email: str
    password: str


class LoginRequest(BaseModel):

    email: str
    password: str


# =========================
# REGISTER
# =========================

@router.post("/register")
def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):

    # Check existing email

    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Hash password

    password_hash = bcrypt.hashpw(
        user_data.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    # Create user

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.id
    }


# =========================
# LOGIN
# =========================

@router.post("/login")
def login(
    user_data: LoginRequest,
    db: Session = Depends(get_db)
):

    # Find user

    user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Verify password

    password_correct = bcrypt.checkpw(
        user_data.password.encode("utf-8"),
        user.password_hash.encode("utf-8")
    )

    if not password_correct:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "message": "Login successful",
        "user_id": user.id,
        "name": user.name,
        "email": user.email
    }