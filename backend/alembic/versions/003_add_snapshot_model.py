"""
add snapshot model

Revision ID: 003_add_snapshot_model
Revises: 002_add_application_settings
Create Date: 2025-07-01
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_add_snapshot_model'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'snapshots',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('camera_id', sa.Integer(), sa.ForeignKey('cameras.id'), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('taken_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table('snapshots') 