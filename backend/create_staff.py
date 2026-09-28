from getpass import getpass

from sqlalchemy import select, func

from app.db import SessionLocal
from app.models import User, Role, LegalOfficer, Counsellor
from app.security import passwords, audit


def main():
    print("1. Lawyer / Legal Officer")
    print("2. Counsellor")
    choice = input("Choose 1 or 2: ").strip()

    if choice not in {"1", "2"}:
        print("Invalid choice.")
        return

    name = input("Full name: ").strip()
    email = input("Email: ").strip().lower()

    if not name or len(name) > 120:
        print("Name must contain 1–120 characters.")
        return

    if "@" not in email or len(email) > 254:
        print("Enter a valid email address.")
        return

    password = getpass("Password (at least 12 characters): ")
    confirmation = getpass("Confirm password: ")

    if len(password) < 12:
        print("Password must contain at least 12 characters.")
        return

    if password != confirmation:
        print("Passwords do not match.")
        return

    role = (
        Role.LEGAL_OFFICER
        if choice == "1"
        else Role.COUNSELLOR
    )

    with SessionLocal() as db:
        existing = db.scalar(
            select(User).where(func.lower(User.email) == email)
        )

        if existing:
            print("That email already has an account. Nothing changed.")
            return

        user = User(
            name=name,
            email=email,
            password_hash=passwords.hash(password),
            role=role,
            active=True,
        )
        db.add(user)
        db.flush()

        if role == Role.LEGAL_OFFICER:
            profile = LegalOfficer(
                user_id=user.id,
                designation="Legal Officer",
            )
        else:
            profile = Counsellor(
                user_id=user.id,
                specialization="General counselling",
            )

        db.add(profile)
        db.flush()

        audit(db, None, "CREATE_STAFF_LOCAL", "user", user.id)
        db.commit()

        print(f"Created {role.value} account: {email}")


if __name__ == "__main__":
    main()