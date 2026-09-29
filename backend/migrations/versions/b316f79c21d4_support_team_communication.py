"""Staff contact phone and indexed support-team conversations."""
from alembic import op
import sqlalchemy as sa

revision = 'b316f79c21d4'
down_revision = '86d8e04f1741'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(32), nullable=True))
    op.create_index('ix_chat_messages_pair_time', 'chat_messages', ['victim_id', 'sender_id', 'recipient_id', 'created_at'])


def downgrade():
    op.drop_index('ix_chat_messages_pair_time', table_name='chat_messages')
    op.drop_column('users', 'phone')
