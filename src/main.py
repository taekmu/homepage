from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import uvicorn

app = FastAPI(title="User API")

# =========================
# Pydantic Models
# =========================

class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    id: int

class UserResponse(UserBase):
    id: int


# =========================
# In-Memory DB (예제용)
# =========================

users: Dict[int, UserResponse] = {
    1: UserResponse(id=1, name="John Doe"),
    2: UserResponse(id=2, name="Jane Doe"),
}

# =========================
# API Endpoints
# =========================

@app.get("/users", response_model=list[UserResponse])
def get_all_users():
    return list(users.values())


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return users[user_id]


@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):
    if user.id in users:
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = UserResponse(id=user.id, name=user.name)
    users[user.id] = new_user
    return new_user


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserBase):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user = UserResponse(id=user_id, name=user.name)
    users[user_id] = updated_user
    return updated_user


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    del users[user_id]
    return


# =========================
# Run Server
# =========================

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)