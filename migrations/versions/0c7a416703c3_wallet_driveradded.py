"""'wallet_driveradded'

Revision ID: 0c7a416703c3
Revises: 145c4c8ddb64
Create Date: 2024-08-05 11:44:14.347629

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c7a416703c3'
down_revision = '145c4c8ddb64'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('wallet', schema=None) as batch_op:
        batch_op.add_column(sa.Column('driver_id', sa.Integer(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('wallet', schema=None) as batch_op:
        batch_op.drop_column('driver_id')

    # ### end Alembic commands ###