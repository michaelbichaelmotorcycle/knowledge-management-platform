from getpass import getpass

from app.db.database import SessionLocal
from app.models.user import User
from app.services.auth import get_password_hash


def main():
    username = input("Admin username: ").strip()
    password = getpass("Admin password: ")

    if not username:
        print("Username is required.")
        return

    if not password:
        print("Password is required.")
        return

    db = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        if existing_user:
            print(f"User '{username}' already exists.")
            return

        user = User(
            username=username,
            hashed_password=get_password_hash(password),
            role="admin",
            disabled=False,
        )

        db.add(user)
        db.commit()

        print(f"Admin user '{username}' created successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
