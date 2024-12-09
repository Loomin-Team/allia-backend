from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os
from app.auth.schemas.auth_schemas import Token, UserSchemaPost, CreateUserRequest
from app.auth.services.auth_services import AuthServices
from app.config.db import get_db

auth = APIRouter()

SECRET_KEY = os.getenv('SECRET_KEY')  # Ya no se necesita hardcodear
ALGORITHM = os.getenv('ALGORITHM')

endpoint = "/auth"

@auth.post(endpoint + '/sign-up', status_code=status.HTTP_201_CREATED, response_model=Token, tags=["Auth"])
async def sign_up(create_user_request: UserSchemaPost, db: Session = Depends(get_db)):
    new_user = await AuthServices.sign_up(create_user_request=create_user_request, db=db)
    return new_user

@auth.post(endpoint + '/sign-in', status_code=status.HTTP_200_OK, response_model=Token, tags=["Auth"])
async def sign_in(create_user_request: CreateUserRequest, db: Session = Depends(get_db)):
    token = await AuthServices.sign_in(create_user_request=create_user_request, db=db)
    return token