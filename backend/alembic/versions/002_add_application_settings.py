"""add application settings

Revision ID: 002
Revises: c4871d902e44
Create Date: 2024-06-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '002'
down_revision = 'c4871d902e44'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table already exists
    inspector = inspect(op.get_bind())
    if 'application_settings' not in inspector.get_table_names():
        # Create application_settings table
        op.create_table('application_settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('auto_start_streams', sa.Boolean(), nullable=False, default=False),
            sa.Column('stream_quality', sa.String(), nullable=False, default='medium'),
            sa.Column('store_data_on_camera', sa.Boolean(), nullable=False, default=True),
            sa.Column('auto_download_events', sa.Boolean(), nullable=False, default=False),
            sa.Column('auto_download_snapshots', sa.Boolean(), nullable=False, default=False),
            sa.Column('event_retention_days', sa.Integer(), nullable=False, default=30),
            sa.Column('snapshot_retention_days', sa.Integer(), nullable=False, default=7),
            sa.Column('mobile_data_saving', sa.Boolean(), nullable=False, default=True),
            sa.Column('low_bandwidth_mode', sa.Boolean(), nullable=False, default=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    # Drop application_settings table
    op.drop_table('application_settings') 