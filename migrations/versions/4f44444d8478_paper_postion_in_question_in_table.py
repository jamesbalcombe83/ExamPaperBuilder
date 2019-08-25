"""paper postion in question_in table

Revision ID: 4f44444d8478
Revises: 0fcdc3e64762
Create Date: 2019-08-14 10:24:18.194265

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f44444d8478'
down_revision = '0fcdc3e64762'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('question_in', schema=None) as batch_op:
        batch_op.add_column(sa.Column('paper_position', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('question_in', schema=None) as batch_op:
        batch_op.drop_column('paper_position')

    # ### end Alembic commands ###