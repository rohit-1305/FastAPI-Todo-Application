from typing import Annotated 
from pydantic import BaseModel, Field 
from sqlalchemy.orm import Session 
from fastapi import APIRouter, Depends, HTTPException, Path 
from starlette import status 
from models import Todos
from .auth import get_current_user 
from database import SessionLocal 

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

# This is used for validation of todo request fields
class TodoRequest(BaseModel):
    title : str = Field(min_length = 3)
    description : str = Field(min_length = 3, max_length = 100)
    priority :int = Field(gt=0, lt=6)
    complete : bool 

''' CRUD Operations on Todos'''
@router.get("/",status_code = status.HTTP_200_OK)
async def read_all(user: user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Authentication Failed")
    return db.query(Todos).filter(Todos.owner_id == user.get('id')).all()



@router.get("/todo/{todo_id}", status_code = status.HTTP_200_OK)
async def read_todo(user:user_dependency,db:db_dependency, todo_id : int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Authentication Failed")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Todo with id {todo_id} is not found")
    return todo_model

@router.post("/todo", status_code = status.HTTP_201_CREATED)
async def create_todo(user:user_dependency, db:db_dependency,todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Authentication Failed")
    todo_model = Todos(**todo_request.model_dump(), owner_id = user.get('id'))
    db.add(todo_model)
    db.commit()
    

@router.put("/todo/{todo_id}", status_code = status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency,db:db_dependency, todo_request = TodoRequest, todo_id : int= Path(gt=0)):
    if user is None:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Authentication Failed")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status = 404, detail = 'Todo Not Found')

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()

@router.delete("/todo/{todo_id}", status_code= status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency,db:db_dependency, todo_id : int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Authentication Failed")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status = 404, detail='Todo not found')
    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()