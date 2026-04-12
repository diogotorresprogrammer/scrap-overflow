"""initial schema

Revision ID: b98f6e1b351c
Revises:
Create Date: 2026-04-12 17:20:01.535938

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b98f6e1b351c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('email', name=op.f('uq_users_email')),
        sa.UniqueConstraint('username', name=op.f('uq_users_username')),
    )
    op.create_table('donators',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('contact', sa.String(length=200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_donators_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_donators')),
    )
    op.create_table('projects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_projects_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_projects')),
    )
    op.create_table('items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('item_type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dimension_raw', sa.String(length=100), nullable=True),
        sa.Column('dimension_parsed', sa.JSON(), nullable=True),
        sa.Column('dimension_unit', sa.String(length=10), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('location_lat', sa.Float(), nullable=True),
        sa.Column('location_lng', sa.Float(), nullable=True),
        sa.Column('condition', sa.String(length=50), nullable=True),
        sa.Column('photo_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_donation', sa.Boolean(), nullable=False),
        sa.Column('donator_id', sa.UUID(), nullable=True),
        sa.Column('donated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('allocated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consumed', sa.Boolean(), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['donator_id'], ['donators.id'], name=op.f('fk_items_donator_id_donators')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_items_project_id_projects')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_items_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_items')),
    )
    op.create_table('lumber_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('species', sa.String(length=100), nullable=True),
        sa.Column('length', sa.Float(), nullable=True),
        sa.Column('width', sa.Float(), nullable=True),
        sa.Column('thickness', sa.Float(), nullable=True),
        sa.Column('grade', sa.String(length=50), nullable=True),
        sa.Column('is_treated', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['items.id'], name=op.f('fk_lumber_items_id_items')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_lumber_items')),
    )
    op.create_table('metal_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('metal_type', sa.String(length=100), nullable=True),
        sa.Column('profile', sa.String(length=100), nullable=True),
        sa.Column('length', sa.Float(), nullable=True),
        sa.Column('width', sa.Float(), nullable=True),
        sa.Column('thickness', sa.Float(), nullable=True),
        sa.Column('alloy', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['items.id'], name=op.f('fk_metal_items_id_items')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_metal_items')),
    )
    op.create_table('furniture_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('furniture_type', sa.String(length=100), nullable=True),
        sa.Column('material', sa.String(length=100), nullable=True),
        sa.Column('style', sa.String(length=100), nullable=True),
        sa.Column('num_pieces', sa.Integer(), nullable=True),
        sa.Column('has_hardware', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['items.id'], name=op.f('fk_furniture_items_id_items')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_furniture_items')),
    )
    op.create_table('appliance_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('appliance_type', sa.String(length=100), nullable=True),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('model_number', sa.String(length=100), nullable=True),
        sa.Column('working_condition', sa.String(length=50), nullable=True),
        sa.Column('voltage', sa.Integer(), nullable=True),
        sa.Column('amperage', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['items.id'], name=op.f('fk_appliance_items_id_items')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_appliance_items')),
    )
    op.create_table('project_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('item_type', sa.String(length=50), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('matched_item_id', sa.UUID(), nullable=True),
        sa.Column('matched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['matched_item_id'], ['items.id'], name=op.f('fk_project_items_matched_item_id_items')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_project_items_project_id_projects')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_project_items')),
    )


def downgrade() -> None:
    op.drop_table('project_items')
    op.drop_table('appliance_items')
    op.drop_table('furniture_items')
    op.drop_table('metal_items')
    op.drop_table('lumber_items')
    op.drop_table('items')
    op.drop_table('projects')
    op.drop_table('donators')
    op.drop_table('users')
