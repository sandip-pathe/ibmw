import os
import requests
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from jose import jwt

NEON_DATA_API_URL = os.getenv("NEON_DATA_API_URL")
NEON_API_KEY = os.getenv("NEON_API_KEY")
STACK_JWKS_URL = os.getenv("STACK_JWKS_URL")

router = APIRouter(prefix="/auth", tags=["auth"])

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

def neon_query(sql: str, params=None):
    headers = {"Authorization": f"Bearer {NEON_API_KEY}", "Content-Type": "application/json"}
    payload = {"sql": sql}
    if params:
        payload["params"] = params
    resp = requests.post(f"{NEON_DATA_API_URL}/sql", json=payload, headers=headers)
    if not resp.ok:
        raise HTTPException(status_code=500, detail=f"Neon API error: {resp.text}")
    return resp.json()

def issue_stack_auth_token(user_id: str):
    # TODO: Integrate with Stack Auth API to issue JWT
    # For now, return a dummy token
    return jwt.encode({"sub": user_id}, "dummy_secret", algorithm="HS256")

def verify_stack_auth_token(token: str):
    # TODO: Validate JWT using Stack Auth JWKS
    # For now, decode with dummy secret
    try:
        payload = jwt.decode(token, "dummy_secret", algorithms=["HS256"])
        return payload.get("sub")
    except Exception:
        return None

@router.post("/signup", response_model=Token)
def signup(user: UserCreate):
    # Check if user exists
    sql = "SELECT user_id FROM users WHERE email = $1"
    result = neon_query(sql, [user.email])
    if result["results"]:
        raise HTTPException(status_code=400, detail="Email already registered")
    # Insert user
    user_id = user.email  # Use email as user_id for Stack Auth
    sql = "INSERT INTO users (user_id, email, password) VALUES ($1, $2, $3) RETURNING user_id"
    neon_query(sql, [user_id, user.email, user.password])
    token = issue_stack_auth_token(user_id)
    return Token(access_token=token)

@router.post("/login", response_model=Token)
def login(user: UserLogin):
    sql = "SELECT user_id, password FROM users WHERE email = $1"
    result = neon_query(sql, [user.email])
    if not result["results"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    db_user = result["results"][0]
    if db_user["password"] != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = issue_stack_auth_token(db_user["user_id"])
    return Token(access_token=token)

@router.get("/me")
def get_me(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = verify_stack_auth_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    sql = "SELECT email FROM users WHERE user_id = $1"
    result = neon_query(sql, [user_id])
    if not result["results"]:
        raise HTTPException(status_code=404, detail="User not found")
    return {"email": result["results"][0]["email"]}
