"""'wallet_added'

Revision ID: 4c9f3d7edb3d
Revises: 34277aad148d
Create Date: 2024-08-05 11:36:45.800239

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4c9f3d7edb3d'
down_revision = '34277aad148d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('wallet',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('from_date', sa.DateTime(), nullable=False),
    sa.Column('to_date', sa.DateTime(), nullable=False),
    sa.Column('amount', mysql.DECIMAL(precision=10, scale=2), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('wallet')
    # ### end Alembic commands ###
