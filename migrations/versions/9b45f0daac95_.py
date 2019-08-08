"""empty message

Revision ID: 9b45f0daac95
Revises: 413563ba333b
Create Date: 2019-08-08 23:35:47.193284

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b45f0daac95'
down_revision = '413563ba333b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('pin_data', 'cursor',
               existing_type=sa.VARCHAR(length=300),
               nullable=False)
    op.alter_column('pin_data', 'destination_board',
               existing_type=sa.VARCHAR(length=300),
               nullable=False)
    op.alter_column('pin_data', 'source_board',
               existing_type=sa.VARCHAR(length=300),
               nullable=False)
    op.alter_column('pinterest_data', 'first_name',
               existing_type=sa.VARCHAR(length=300),
               nullable=False)
    op.alter_column('pinterest_data', 'last_name',
               existing_type=sa.VARCHAR(length=300),
               nullable=False)
    op.alter_column('pinterest_data', 'username',
               existing_type=sa.VARCHAR(length=300),
               nullable=False)
    op.alter_column('roles', 'name',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    op.alter_column('tokens', 'token',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('tokens', 'token',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
    op.alter_column('roles', 'name',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    op.alter_column('pinterest_data', 'username',
               existing_type=sa.VARCHAR(length=300),
               nullable=True)
    op.alter_column('pinterest_data', 'last_name',
               existing_type=sa.VARCHAR(length=300),
               nullable=True)
    op.alter_column('pinterest_data', 'first_name',
               existing_type=sa.VARCHAR(length=300),
               nullable=True)
    op.alter_column('pin_data', 'source_board',
               existing_type=sa.VARCHAR(length=300),
               nullable=True)
    op.alter_column('pin_data', 'destination_board',
               existing_type=sa.VARCHAR(length=300),
               nullable=True)
    op.alter_column('pin_data', 'cursor',
               existing_type=sa.VARCHAR(length=300),
               nullable=True)
    # ### end Alembic commands ###