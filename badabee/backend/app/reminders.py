"""Run periodically: python -m app.reminders. In-app only; no external messages."""
from datetime import timedelta
from uuid import NAMESPACE_URL, uuid5
from sqlalchemy import select
from .models import Victim, WellbeingCheckin, Followup, Notification, NotificationOutbox, now
from .notifications import deliver_in_app


def queue_reminder(db, recipient, key, title):
    reminder_id = str(uuid5(NAMESPACE_URL, 'badabee-reminder:' + key))
    if db.get(Notification, reminder_id):
        return False
    db.add(Notification(id=reminder_id, user_id=recipient, title=title))
    db.flush()
    db.add(NotificationOutbox(notification_id=reminder_id))
    return True


def run_reminders(db):
    clock = now()
    count = 0
    for victim in db.scalars(select(Victim)):
        checkin = db.scalar(select(WellbeingCheckin).where(WellbeingCheckin.victim_id == victim.id).order_by(WellbeingCheckin.created_at.desc()))
        if not checkin or checkin.created_at + timedelta(days=7) <= clock:
            count += queue_reminder(db, victim.user_id, f'weekly:{victim.id}:{clock.strftime("%G-%V")}', 'Your weekly wellbeing check-in is due.')
        for followup in db.scalars(select(Followup).where(Followup.victim_id == victim.id,
                Followup.status == 'PENDING', Followup.due_at >= clock, Followup.due_at <= clock + timedelta(days=1))):
            count += queue_reminder(db, victim.user_id, f'followup:{followup.id}:{followup.due_at.isoformat()}', 'A follow-up is scheduled within the next 24 hours.')
    db.flush()
    deliver_in_app(db)
    return count


if __name__ == '__main__':
    from .db import SessionLocal
    with SessionLocal.begin() as db:
        print(f'Created {run_reminders(db)} in-app reminders')
