import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/qqpet")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="QQ Pet Admin Panel")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


TEMPLATE_DIR = Path(__file__).parent / "templates"


class UserOut(BaseModel):
    id: int
    username: str
    email: str | None
    is_active: bool
    exists_pet: bool
    created_at: str | None
    last_login_at: str | None


@app.get("/", response_class=HTMLResponse)
def admin_page():
    html = (TEMPLATE_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.get("/api/users")
def list_users():
    db = next(get_db())
    try:
        rows = db.execute(text("""
            SELECT u.id, u.username, u.email, u.is_active,
                   u.created_at, u.last_login_at,
                   CASE WHEN p.id IS NOT NULL THEN true ELSE false END AS exists_pet
            FROM users u
            LEFT JOIN pet_data p ON p.user_id = u.id
            ORDER BY u.id
        """)).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@app.post("/api/users/{user_id}/toggle")
def toggle_user(user_id: int):
    db = next(get_db())
    try:
        row = db.execute(text("SELECT id, is_active FROM users WHERE id = :id"),
                         {"id": user_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")
        new_active = not row.is_active
        db.execute(text("UPDATE users SET is_active = :active WHERE id = :id"),
                   {"active": new_active, "id": user_id})
        db.commit()
        return {"ok": True, "is_active": new_active}
    finally:
        db.close()


@app.delete("/api/users/{user_id}")
def delete_user(user_id: int):
    db = next(get_db())
    try:
        row = db.execute(text("SELECT id FROM users WHERE id = :id"),
                         {"id": user_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")
        db.execute(text("DELETE FROM sessions WHERE user_id = :id"), {"id": user_id})
        db.execute(text("DELETE FROM pet_inventory WHERE user_id = :id"), {"id": user_id})
        db.execute(text("DELETE FROM pet_data WHERE user_id = :id"), {"id": user_id})
        db.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        db.commit()
        return {"ok": True, "message": f"用户 {user_id} 已删除"}
    finally:
        db.close()


@app.post("/api/users/purge-inactive")
def purge_inactive():
    db = next(get_db())
    try:
        ids = db.execute(text("SELECT id FROM users WHERE is_active = false")).fetchall()
        ids = [r.id for r in ids]
        if not ids:
            return {"ok": True, "deleted": 0, "message": "没有未激活用户"}
        for uid in ids:
            db.execute(text("DELETE FROM sessions WHERE user_id = :id"), {"id": uid})
            db.execute(text("DELETE FROM pet_inventory WHERE user_id = :id"), {"id": uid})
            db.execute(text("DELETE FROM pet_data WHERE user_id = :id"), {"id": uid})
        db.execute(text("DELETE FROM users WHERE is_active = false"))
        db.commit()
        return {"ok": True, "deleted": len(ids), "message": f"已清除 {len(ids)} 个未激活用户"}
    finally:
        db.close()
