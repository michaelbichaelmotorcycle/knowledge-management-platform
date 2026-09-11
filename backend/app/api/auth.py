from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.auth import (
    authenticate_user,
    create_access_token,
    get_db,
    get_current_user,
)


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    access_token = create_access_token(
        username=user.username,
        role=user.role,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me")
def read_current_user(
    current_user=Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "disabled": current_user.disabled,
    }
