"""empty message

Revision ID: fced7eea1ca7
Revises: 655d2e39050e
Create Date: 2019-09-18 00:37:24.762036

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fced7eea1ca7"
down_revision = "655d2e39050e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("flavors", sa.Column("color2", sa.String(length=20), nullable=True))
    op.drop_column("flavors", "color")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("flavors", sa.Column("color", sa.VARCHAR(length=6), autoincrement=False, nullable=True))
    op.drop_column("flavors", "color2")
    # ### end Alembic commands ###