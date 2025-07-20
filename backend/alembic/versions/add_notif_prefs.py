"""add notification preference fields

Revision ID: add_notification_preference_fields
Revises: c4871d902e44
Create Date: 2025-07-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_notif_prefs'
down_revision = 'a0a3380ae8be'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new notification preference columns to users table
    op.add_column('users', sa.Column('event_notifications', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('camera_status_notifications', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('system_alerts', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    # Remove the columns if needed
    op.drop_column('users', 'system_alerts')
    op.drop_column('users', 'camera_status_notifications')
    op.drop_column('users', 'event_notifications') 