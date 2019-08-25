"""exam level update

Revision ID: 6afcde9fe77b
Revises: 8fb7fe09c39f
Create Date: 2019-08-06 12:45:34.189181

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6afcde9fe77b'
down_revision = '8fb7fe09c39f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('exam_levels',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exam_levels_name'), 'exam_levels', ['name'], unique=True)
    op.add_column('paper', sa.Column('exam_level', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'paper', 'exam_levels', ['exam_level'], ['id'])
    op.add_column('question', sa.Column('exam_level', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'question', 'exam_levels', ['exam_level'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'question', type_='foreignkey')
    op.drop_column('question', 'exam_level')
    op.drop_constraint(None, 'paper', type_='foreignkey')
    op.drop_column('paper', 'exam_level')
    op.drop_index(op.f('ix_exam_levels_name'), table_name='exam_levels')
    op.drop_table('exam_levels')
    # ### end Alembic commands ###