"""用户管理脚本 - 用于创建和管理用户"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.core.security import get_password_hash
from app.models import User


def create_user(username: str, password: str, email: str = None, is_admin: bool = False) -> User:
    """创建新用户"""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise ValueError(f"用户名 '{username}' 已存在")
        
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=is_admin
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"用户 '{username}' 创建成功！")
        print(f"  ID: {user.id}")
        print(f"  管理员: {'是' if user.is_admin else '否'}")
        if user.email:
            print(f"  邮箱: {user.email}")
        
        return user
    finally:
        db.close()


def list_users():
    """列出所有用户"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            print("没有用户")
            return
        
        print(f"\n共有 {len(users)} 个用户:\n")
        print(f"{'ID':<5} {'用户名':<20} {'管理员':<8} {'状态':<8} {'邮箱'}")
        print("-" * 80)
        for user in users:
            print(f"{user.id:<5} {user.username:<20} {'是' if user.is_admin else '否':<8} {'活跃' if user.is_active else '禁用':<8} {user.email or '-'}")
        print()
    finally:
        db.close()


def update_password(username: str, new_password: str):
    """更新用户密码"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise ValueError(f"用户 '{username}' 不存在")
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        print(f"用户 '{username}' 密码已更新")
    finally:
        db.close()


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python create_user.py list")
        print("  python create_user.py create <用户名> <密码> [邮箱] [--admin]")
        print("  python create_user.py passwd <用户名> <新密码>")
        print("\n示例:")
        print("  python create_user.py list")
        print("  python create_user.py create admin mypassword admin@example.com --admin")
        print("  python create_user.py create user1 password123")
        print("  python create_user.py passwd admin newpassword")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        list_users()
    
    elif command == "create":
        if len(sys.argv) < 4:
            print("用法: python create_user.py create <用户名> <密码> [邮箱] [--admin]")
            sys.exit(1)
        
        username = sys.argv[2]
        password = sys.argv[3]
        email = None
        is_admin = False
        
        for arg in sys.argv[4:]:
            if arg == "--admin":
                is_admin = True
            elif "@" in arg:
                email = arg
        
        create_user(username, password, email, is_admin)
    
    elif command == "passwd":
        if len(sys.argv) < 4:
            print("用法: python create_user.py passwd <用户名> <新密码>")
            sys.exit(1)
        
        username = sys.argv[2]
        new_password = sys.argv[3]
        update_password(username, new_password)
    
    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
