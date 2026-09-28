"""Add private per-user profile preferences and photo storage."""
from alembic import op
import sqlalchemy as sa

revision = '72ac9e13'
down_revision = '0b9345094ff9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_settings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('photo', sa.Text(), nullable=True),
        sa.Column('language', sa.String(60), nullable=False),
        sa.Column('theme', sa.String(20), nullable=False),
        sa.Column('text_size', sa.String(20), nullable=False),
        sa.Column('high_contrast', sa.Boolean(), nullable=False),
        sa.Column('reduced_motion', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table('user_settings')
