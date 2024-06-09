from typing import Annotated 
from pydantic import BaseModel, Field 
from sqlalchemy.orm import Session 
from fastapi import APIRouter, Depends, HTTPException, Path 
from starlette import status 
from models import Todos
from .auth import get_current_user 
from database import SessionLocal 

router = APIRouter(
    prefix = '/admin',
    tags = ['Admin']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/todo", status_code = status.HTTP_200_OK)
async def read_all(user: user_dependency, db : db_dependency):
    if user is None or user.get('user_role')!= 'admin':
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Authentication Failed")
    return db.query(Todos).all()

@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(user : user_dependency, db : db_dependency, todo_id : int = Path(gt=0)):
    if user is None or user.get('user_role')!= 'admin':
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Authentication Failed")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    return todo_model

@router.delete("/todo/{todo_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_todo(user : user_dependency, db : db_dependency, todo_id : int = Path(gt=0)):
    if user is None or user.get('user_role')!= 'admin':
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Authentication Failed")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Todo with id {todo_id} is not found")
    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()