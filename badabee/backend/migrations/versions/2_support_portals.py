"""Support check-ins, care actions and grounded chat."""
from alembic import op
import sqlalchemy as sa

revision = '2_support_portals'
down_revision = '0b9345094ff9'
branch_labels = None
depends_on = None


def record_columns():
    return [sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)]


def upgrade():
    op.add_column('followups', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_table('wellbeing_checkins', *record_columns(),
        sa.Column('victim_id', sa.String(36), sa.ForeignKey('victims.id'), nullable=False),
        sa.Column('request_id', sa.String(80), nullable=False),
        sa.Column('mood', sa.Integer, nullable=False), sa.Column('stress', sa.Integer, nullable=False),
        sa.Column('sleep', sa.Integer, nullable=False), sa.Column('feels_unsafe', sa.Boolean, nullable=False),
        sa.Column('text', sa.Text, nullable=False), sa.Column('language', sa.String(10), nullable=False),
        sa.Column('prediction_id', sa.String(36), sa.ForeignKey('distress_predictions.id'), nullable=False),
        sa.UniqueConstraint('victim_id', 'request_id'),
        sa.CheckConstraint('mood BETWEEN 1 AND 5 AND stress BETWEEN 1 AND 5 AND sleep BETWEEN 1 AND 5'))
    op.create_index('ix_wellbeing_checkins_victim_id', 'wellbeing_checkins', ['victim_id'])
    op.create_table('support_actions', *record_columns(),
        sa.Column('victim_id', sa.String(36), sa.ForeignKey('victims.id'), nullable=False),
        sa.Column('actor_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('kind', sa.String(30), nullable=False), sa.Column('note', sa.Text, nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('ngo_id', sa.String(36), sa.ForeignKey('ngos.id')),
        sa.Column('resolved_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('resolved_at', sa.DateTime(timezone=True)))
    op.create_index('ix_support_actions_victim_id', 'support_actions', ['victim_id'])
    op.create_table('support_chat_turns', *record_columns(),
        sa.Column('victim_id', sa.String(36), sa.ForeignKey('victims.id'), nullable=False),
        sa.Column('request_id', sa.String(80), nullable=False), sa.Column('message', sa.Text, nullable=False),
        sa.Column('reply', sa.Text, nullable=False), sa.Column('language', sa.String(10), nullable=False),
        sa.Column('intent', sa.String(40), nullable=False), sa.UniqueConstraint('victim_id', 'request_id'))
    op.create_index('ix_support_chat_turns_victim_id', 'support_chat_turns', ['victim_id'])


def downgrade():
    for name in ('support_chat_turns', 'support_actions', 'wellbeing_checkins'):
        op.drop_table(name)
    op.drop_column('followups', 'completed_at')
