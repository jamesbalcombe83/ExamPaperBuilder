"""setup

Revision ID: 5a6be900ac2d
Revises: 
Create Date: 2019-08-06 12:55:55.485149

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a6be900ac2d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('exam_boards',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('exam_boards', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_exam_boards_name'), ['name'], unique=True)

    op.create_table('exam_levels',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('exam_levels', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_exam_levels_name'), ['name'], unique=True)

    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('name', sa.String(length=30), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('school_name', sa.String(length=255), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)

    op.create_table('paper',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('exam_level', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('total_marks', sa.Integer(), nullable=True),
    sa.Column('date_created', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['exam_level'], ['exam_levels.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('paper', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_paper_date_created'), ['date_created'], unique=False)
        batch_op.create_index(batch_op.f('ix_paper_name'), ['name'], unique=False)

    op.create_table('question',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('exam_board', sa.Integer(), nullable=True),
    sa.Column('exam_level', sa.Integer(), nullable=True),
    sa.Column('exam_year', sa.Integer(), nullable=True),
    sa.Column('exam_session', sa.Integer(), nullable=True),
    sa.Column('body', sa.String(length=255), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('marks', sa.Integer(), nullable=True),
    sa.Column('answer', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['exam_board'], ['exam_boards.id'], ),
    sa.ForeignKeyConstraint(['exam_level'], ['exam_levels.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_question_timestamp'), ['timestamp'], unique=False)

    op.create_table('question_in',
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('paper_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['paper_id'], ['paper.id'], ),
    sa.ForeignKeyConstraint(['question_id'], ['question.id'], ),
    sa.PrimaryKeyConstraint('question_id', 'paper_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('question_in')
    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_question_timestamp'))

    op.drop_table('question')
    with op.batch_alter_table('paper', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_paper_name'))
        batch_op.drop_index(batch_op.f('ix_paper_date_created'))

    op.drop_table('paper')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_username'))
        batch_op.drop_index(batch_op.f('ix_user_email'))

    op.drop_table('user')
    with op.batch_alter_table('exam_levels', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_exam_levels_name'))

    op.drop_table('exam_levels')
    with op.batch_alter_table('exam_boards', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_exam_boards_name'))

    op.drop_table('exam_boards')
    # ### end Alembic commands ###
