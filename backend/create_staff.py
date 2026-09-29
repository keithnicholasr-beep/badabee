from getpass import getpass

from sqlalchemy import select, func

from app.db import SessionLocal
from app.models import User, Role, LegalOfficer, Counsellor, LawEnforcementOfficer, District, State
from app.security import passwords, audit


def main():
    print("1. Lawyer / Legal Officer")
    print("2. Counsellor")
    print("3. Law Enforcement Officer")
    choice = input("Choose 1, 2 or 3: ").strip()

    if choice not in {"1", "2", "3"}:
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

    role = {"1": Role.LEGAL_OFFICER, "2": Role.COUNSELLOR, "3": Role.LAW_ENFORCEMENT}[choice]

    with SessionLocal() as db:
        existing = db.scalar(
            select(User).where(func.lower(User.email) == email)
        )

        if existing:
            print("That email already has an account. Nothing changed.")
            return

        district = None
        station = None
        if role == Role.LAW_ENFORCEMENT:
            districts = list(db.scalars(select(District).order_by(District.name)))
            if not districts:
                print("Create districts before adding a law enforcement officer.")
                return
            for index, item in enumerate(districts, 1):
                print(f"{index}. {item.name}, {db.get(State, item.state_id).name}")
            selected = input("District number: ").strip()
            if not selected.isdigit() or not 1 <= int(selected) <= len(districts):
                print("Invalid district.")
                return
            district = districts[int(selected) - 1]
            station = input("Police station: ").strip()
            if not 2 <= len(station) <= 160:
                print("Police station must contain 2-160 characters.")
                return

        user = User(
            name=name,
            email=email,
            password_hash=passwords.hash(password),
            role=role,
            active=True,
            district_id=district.id if district else None,
            state_id=district.state_id if district else None,
        )
        db.add(user)
        db.flush()

        if role == Role.LEGAL_OFFICER:
            profile = LegalOfficer(
                user_id=user.id,
                designation="Legal Officer",
            )
        elif role == Role.LAW_ENFORCEMENT:
            profile = LawEnforcementOfficer(user_id=user.id, police_station=station)
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