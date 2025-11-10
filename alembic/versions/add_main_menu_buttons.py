"""add_main_menu_buttons

Revision ID: add_main_menu_buttons
Revises: 
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5c6f0b12345'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create main_menu_buttons table
    op.create_table(
        'main_menu_buttons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name_ru', sa.String(length=255), nullable=False),
        sa.Column('name_uz', sa.String(length=255), nullable=False),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('callback_data', sa.String(length=255), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_main_menu_buttons_id'), 'main_menu_buttons', ['id'], unique=False)
    op.create_index(op.f('ix_main_menu_buttons_is_active'), 'main_menu_buttons', ['is_active'], unique=False)
    op.create_index(op.f('ix_main_menu_buttons_order_index'), 'main_menu_buttons', ['order_index'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_main_menu_buttons_order_index'), table_name='main_menu_buttons')
    op.drop_index(op.f('ix_main_menu_buttons_is_active'), table_name='main_menu_buttons')
    op.drop_index(op.f('ix_main_menu_buttons_id'), table_name='main_menu_buttons')
    op.drop_table('main_menu_buttons')
