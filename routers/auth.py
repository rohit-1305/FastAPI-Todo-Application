from fastapi import APIRouter, Depends , HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from models import Users
from database import SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError # type: ignore
from datetime import timedelta, datetime, timezone

router = APIRouter(
    prefix='/auth',
    tags=['Authentication']
)

SECRET_KEY = 'f57a2d96eb959426d8d1172e2c589a4d84b76ae397236f452a2cbf8eed252dd1e0efd6f49a358da66969b73abd8b039ca82c450d7e05f3d74086c130a83bf005'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

# This is used for validation of user request
class CreateUserRequest(BaseModel):
    email: str
    username: str
    password: str
    first_name: str
    last_name: str
    role: str
    phone_number : str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
db_dependency = Annotated[Session, Depends(get_db)]



def authenticate_user(username : str,password : str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password,user.hashed_password):
        return False
    return user

def create_access_token(username : str, user_id : int, role : str,expires_delta : timedelta):
    encode = {
        'sub': username,
        'id': user_id,
        'role': role
    }
    expires = datetime.utcnow() + expires_delta 
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token : Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        username :str = payload.get('sub')
        user_id : int = payload.get('id')
        user_role : str = payload.get('role')
        if username is None and user_id is None:
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = 'Could Not validate User')
        return {'username': username, 'id': user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = 'Could Not validate User')


@router.post("/", status_code = status.HTTP_201_CREATED)
async def create_user(db : db_dependency,create_user_request : CreateUserRequest):
    create_user_model = Users(
        email = create_user_request.email,
        username = create_user_request.username,
        first_name = create_user_request.first_name,
        last_name = create_user_request.last_name,
        role = create_user_request.role,
        hashed_password = bcrypt_context.hash(create_user_request.password),
        is_active = True,
        phone_number = create_user_request.phone_number
    )
    db.add(create_user_model)
    db.commit()
    
@router.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username,form_data.password,db)
    if not user:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = 'Could Not validate User')
    token  = create_access_token(user.username,user.id,user.role, timedelta(minutes=20))
    
    return {"access_token": token, "token_type": "bearer"}