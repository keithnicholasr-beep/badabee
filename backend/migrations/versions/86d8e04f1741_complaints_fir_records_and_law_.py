"""complaints FIR records and law enforcement"""
from alembic import op
import sqlalchemy as sa

revision = '86d8e04f1741'
down_revision = '72ac9e13'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('law_enforcement_officers',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('police_station', sa.String(length=160), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('complaints',
    sa.Column('victim_id', sa.String(length=36), nullable=False),
    sa.Column('district_id', sa.String(length=36), nullable=False),
    sa.Column('officer_id', sa.String(length=36), nullable=True),
    sa.Column('subject', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('incident_date', sa.Date(), nullable=True),
    sa.Column('location', sa.String(length=250), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("status IN ('SUBMITTED', 'IN_REVIEW', 'FIR_REGISTERED', 'CLOSED')"),
    sa.ForeignKeyConstraint(['district_id'], ['districts.id'], ),
    sa.ForeignKeyConstraint(['officer_id'], ['law_enforcement_officers.id'], ),
    sa.ForeignKeyConstraint(['victim_id'], ['victims.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_complaints_district_id'), 'complaints', ['district_id'], unique=False)
    op.create_index(op.f('ix_complaints_officer_id'), 'complaints', ['officer_id'], unique=False)
    op.create_index(op.f('ix_complaints_victim_id'), 'complaints', ['victim_id'], unique=False)
    op.create_table('complaint_messages',
    sa.Column('complaint_id', sa.String(length=36), nullable=False),
    sa.Column('sender_id', sa.String(length=36), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_complaint_messages_complaint_id'), 'complaint_messages', ['complaint_id'], unique=False)
    op.create_table('fir_registrations',
    sa.Column('complaint_id', sa.String(length=36), nullable=False),
    sa.Column('registered_by', sa.String(length=36), nullable=False),
    sa.Column('district_id', sa.String(length=36), nullable=False),
    sa.Column('number', sa.String(length=80), nullable=False),
    sa.Column('police_station', sa.String(length=160), nullable=False),
    sa.Column('registered_on', sa.Date(), nullable=False),
    sa.Column('registration_year', sa.Integer(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ),
    sa.ForeignKeyConstraint(['district_id'], ['districts.id'], ),
    sa.ForeignKeyConstraint(['registered_by'], ['law_enforcement_officers.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('complaint_id'),
    sa.UniqueConstraint('district_id', 'police_station', 'registration_year', 'number', name='uq_fir_reference')
    )
    op.create_index(op.f('ix_fir_registrations_district_id'), 'fir_registrations', ['district_id'], unique=False)
    # Preserve unnamed jurisdiction checks when SQLite rebuilds this table.
    checks = (sa.CheckConstraint("role != 'DISTRICT_ADMIN' OR district_id IS NOT NULL"),
              sa.CheckConstraint("role != 'STATE_ADMIN' OR state_id IS NOT NULL")) if op.get_bind().dialect.name == 'sqlite' else ()
    with op.batch_alter_table('users', table_args=checks) as batch:
        batch.alter_column('role',
               existing_type=sa.VARCHAR(length=14),
               type_=sa.Enum('VICTIM', 'COUNSELLOR', 'LAW_ENFORCEMENT', 'LEGAL_OFFICER', 'DISTRICT_ADMIN', 'STATE_ADMIN', 'NATIONAL_ADMIN', name='role', native_enum=False),
               existing_nullable=False)

def downgrade():
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM users WHERE role = 'LAW_ENFORCEMENT'")).scalar():
        raise RuntimeError("Remove or reassign law enforcement accounts before downgrading")
    # Preserve unnamed jurisdiction checks when SQLite rebuilds this table.
    checks = (sa.CheckConstraint("role != 'DISTRICT_ADMIN' OR district_id IS NOT NULL"),
              sa.CheckConstraint("role != 'STATE_ADMIN' OR state_id IS NOT NULL")) if op.get_bind().dialect.name == 'sqlite' else ()
    with op.batch_alter_table('users', table_args=checks) as batch:
        batch.alter_column('role',
               existing_type=sa.Enum('VICTIM', 'COUNSELLOR', 'LAW_ENFORCEMENT', 'LEGAL_OFFICER', 'DISTRICT_ADMIN', 'STATE_ADMIN', 'NATIONAL_ADMIN', name='role', native_enum=False),
               type_=sa.VARCHAR(length=14),
               existing_nullable=False)
    op.drop_index(op.f('ix_fir_registrations_district_id'), table_name='fir_registrations')
    op.drop_table('fir_registrations')
    op.drop_index(op.f('ix_complaint_messages_complaint_id'), table_name='complaint_messages')
    op.drop_table('complaint_messages')
    op.drop_index(op.f('ix_complaints_victim_id'), table_name='complaints')
    op.drop_index(op.f('ix_complaints_officer_id'), table_name='complaints')
    op.drop_index(op.f('ix_complaints_district_id'), table_name='complaints')
    op.drop_table('complaints')
    op.drop_table('law_enforcement_officers')
