from getpass import getpass

from sqlalchemy import select

from .db import SessionLocal
from .models import State, District, User, Role
from .security import passwords


# Initial supported locations. Extend this list as needed.
LOCATIONS = {
    'Tamil Nadu': ['Chennai', 'Coimbatore', 'Madurai'],
    'Karnataka': ['Bengaluru Urban', 'Mysuru', 'Dharwad'],
    'Kerala': ['Ernakulam', 'Kozhikode', 'Thiruvananthapuram'],
}


def main():
    print('Create the initial administrator account.')

    name = input('Administrator name: ').strip()
    email = input('Administrator email: ').strip().lower()
    password = getpass('Password (12+ characters): ')
    confirmation = getpass('Confirm password: ')

    if not name or '@' not in email:
        raise SystemExit('Enter a name and a valid email.')

    if len(password) < 12:
        raise SystemExit('Password must contain at least 12 characters.')

    if password != confirmation:
        raise SystemExit('Passwords do not match.')

    with SessionLocal.begin() as db:
        if db.scalar(select(User.id).limit(1)):
            raise SystemExit(
                'Users already exist. Bootstrap is for a fresh database.'
            )

        for state_name, district_names in LOCATIONS.items():
            state = db.scalar(
                select(State).where(State.name == state_name)
            )

            if state is None:
                state = State(name=state_name)
                db.add(state)
                db.flush()

            for district_name in district_names:
                district = db.scalar(
                    select(District).where(
                        District.state_id == state.id,
                        District.name == district_name,
                    )
                )

                if district is None:
                    db.add(
                        District(
                            name=district_name,
                            state_id=state.id,
                        )
                    )

        db.add(
            User(
                name=name,
                email=email,
                password_hash=passwords.hash(password),
                role=Role.NATIONAL_ADMIN,
                active=True,
            )
        )

    print('Locations and administrator created successfully.')


if __name__ == '__main__':
    main()