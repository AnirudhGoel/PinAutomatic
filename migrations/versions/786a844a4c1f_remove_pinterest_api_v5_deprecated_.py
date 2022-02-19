"""Remove Pinterest API v5 deprecated columns from PinterestData model

Revision ID: 786a844a4c1f
Revises: 51f2c1250a6c
Create Date: 2022-02-18 02:08:17.325623

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '786a844a4c1f'
down_revision = '51f2c1250a6c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('pinterest_data', 'followers')
    op.drop_column('pinterest_data', 'full_name')
    op.drop_column('pinterest_data', 'boards')
    op.drop_column('pinterest_data', 'following')
    op.drop_column('pinterest_data', 'pinterest_id')
    op.drop_column('pinterest_data', 'pins')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pinterest_data', sa.Column('pins', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('pinterest_data', sa.Column('pinterest_id', sa.BIGINT(), autoincrement=False, nullable=True))
    op.add_column('pinterest_data', sa.Column('following', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('pinterest_data', sa.Column('boards', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('pinterest_data', sa.Column('full_name', sa.VARCHAR(length=300), autoincrement=False, nullable=False))
    op.add_column('pinterest_data', sa.Column('followers', sa.INTEGER(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###