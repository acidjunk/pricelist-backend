"""empty message

Revision ID: afacc23c2670
Revises: 33cfa1e5d315
Create Date: 2019-11-26 16:27:56.787736

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "afacc23c2670"
down_revision = "33cfa1e5d315"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("categories", sa.Column("order_number", sa.Integer(), nullable=True))
    op.add_column("kind_images", sa.Column("name", sa.String(length=255), nullable=True))
    op.add_column("kind_images", sa.Column("order_number", sa.Integer(), nullable=True))
    op.drop_column("kind_images", "original_name")
    op.add_column("kinds", sa.Column("approved_at", sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("kinds", "approved_at")
    op.add_column("kind_images", sa.Column("original_name", sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.drop_column("kind_images", "order_number")
    op.drop_column("kind_images", "name")
    op.drop_column("categories", "order_number")
    # ### end Alembic commands ###
