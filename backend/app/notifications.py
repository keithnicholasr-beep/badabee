from sqlalchemy import select
from .models import *


def publish_alert(db, prediction):
    if prediction.level not in ('HIGH', 'CRITICAL'):
        return
    alert = Alert(victim_id=prediction.victim_id, prediction_id=prediction.id,
                  severity=prediction.level, message='Distress review requested')
    db.add(alert)
    db.flush()
    recipients = db.scalars(select(Counsellor.user_id).join(CounsellorAssignment,
                           CounsellorAssignment.counsellor_id == Counsellor.id).where(
                           CounsellorAssignment.victim_id == prediction.victim_id, CounsellorAssignment.active.is_(True)))
    for user_id in set(recipients):
        notification = Notification(user_id=user_id, alert_id=alert.id, title='A support review needs your attention')
        db.add(notification)
        db.flush()
        db.add(NotificationOutbox(notification_id=notification.id))


def deliver_in_app(db):
    # Row locks permit safe concurrent workers on PostgreSQL. Delivery and acknowledgement are transactional.
    pending = db.scalars(select(NotificationOutbox).where(NotificationOutbox.status == 'PENDING',
                         NotificationOutbox.channel == 'IN_APP').with_for_update(skip_locked=True).limit(100))
    count = 0
    for row in pending:
        row.status, row.delivered_at = 'DELIVERED', now()
        row.attempts += 1
        count += 1
    return count


if __name__ == '__main__':
    from .db import SessionLocal
    with SessionLocal.begin() as session:
        print(f'Delivered {deliver_in_app(session)} in-app notifications')
