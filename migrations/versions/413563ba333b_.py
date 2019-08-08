"""empty message

Revision ID: 413563ba333b
Revises: 0c355b44c78d
Create Date: 2019-08-08 21:46:54.251365

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '413563ba333b'
down_revision = '0c355b44c78d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pinterest_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('pinterest_id', sa.BigInteger(), nullable=True),
    sa.Column('username', sa.String(length=300), nullable=True),
    sa.Column('first_name', sa.String(length=300), nullable=True),
    sa.Column('last_name', sa.String(length=300), nullable=True),
    sa.Column('pins', sa.Integer(), nullable=True),
    sa.Column('boards', sa.Integer(), nullable=True),
    sa.Column('following', sa.Integer(), nullable=True),
    sa.Column('followers', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pinterest_data_user_id'), 'pinterest_data', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_pinterest_data_user_id'), table_name='pinterest_data')
    op.drop_table('pinterest_data')
    # ### end Alembic commands ###