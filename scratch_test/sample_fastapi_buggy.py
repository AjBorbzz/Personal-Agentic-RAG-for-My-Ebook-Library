from fastapi import FastAPI, Request
import sqlite3

app = FastAPI()


@app.post("/login")
async def login(request: Request):
    data = await request.json()

    username = data["username"]
    password = data["password"]

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)

    user = cursor.fetchone()

    if user:
        return {
            "status": "success",
            "message": "Login successful",
            "user": user,
            "password": password,
        }

    return {
        "status": "failed",
        "message": "Invalid credentials",
    }


@app.get("/users")
def get_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    return {
        "users": users
    }