"""update_settings_with_quality_levels_and_camera_settings

Revision ID: 004
Revises: 100e72eba97c
Create Date: 2025-01-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '100e72eba97c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns as nullable first
    op.add_column('application_settings', sa.Column('live_quality_level', sa.Integer(), nullable=True))
    op.add_column('application_settings', sa.Column('recording_quality_level', sa.Integer(), nullable=True))
    op.add_column('application_settings', sa.Column('heater_level', sa.Integer(), nullable=True))
    op.add_column('application_settings', sa.Column('picture_rotation', sa.Integer(), nullable=True))
    
    # Set default values for existing rows
    op.execute("UPDATE application_settings SET live_quality_level = 50 WHERE live_quality_level IS NULL")
    op.execute("UPDATE application_settings SET recording_quality_level = 50 WHERE recording_quality_level IS NULL")
    op.execute("UPDATE application_settings SET heater_level = 0 WHERE heater_level IS NULL")
    op.execute("UPDATE application_settings SET picture_rotation = 90 WHERE picture_rotation IS NULL")
    
    # Make columns NOT NULL
    op.alter_column('application_settings', 'live_quality_level', nullable=False)
    op.alter_column('application_settings', 'recording_quality_level', nullable=False)
    op.alter_column('application_settings', 'heater_level', nullable=False)
    op.alter_column('application_settings', 'picture_rotation', nullable=False)
    
    # Drop old columns
    op.drop_column('application_settings', 'auto_start_streams')
    op.drop_column('application_settings', 'stream_quality')
    op.drop_column('application_settings', 'auto_download_snapshots')


def downgrade() -> None:
    # Add back old columns
    op.add_column('application_settings', sa.Column('auto_start_streams', sa.Boolean(), nullable=True))
    op.add_column('application_settings', sa.Column('stream_quality', sa.String(), nullable=True))
    op.add_column('application_settings', sa.Column('auto_download_snapshots', sa.Boolean(), nullable=True))
    
    # Set default values for old columns
    op.execute("UPDATE application_settings SET auto_start_streams = false WHERE auto_start_streams IS NULL")
    op.execute("UPDATE application_settings SET stream_quality = 'medium' WHERE stream_quality IS NULL")
    op.execute("UPDATE application_settings SET auto_download_snapshots = false WHERE auto_download_snapshots IS NULL")
    
    # Make old columns NOT NULL
    op.alter_column('application_settings', 'auto_start_streams', nullable=False)
    op.alter_column('application_settings', 'stream_quality', nullable=False)
    op.alter_column('application_settings', 'auto_download_snapshots', nullable=False)
    
    # Drop new columns
    op.drop_column('application_settings', 'picture_rotation')
    op.drop_column('application_settings', 'heater_level')
    op.drop_column('application_settings', 'recording_quality_level')
    op.drop_column('application_settings', 'live_quality_level') 