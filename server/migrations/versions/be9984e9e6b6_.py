"""empty message

Revision ID: be9984e9e6b6
Revises: 132b252067c3
Create Date: 2019-08-26 21:47:37.761331

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'be9984e9e6b6'
down_revision = '132b252067c3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('prices',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=True),
    sa.Column('price', sa.Float(), nullable=True),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prices_id'), 'prices', ['id'], unique=False)
    op.create_index(op.f('ix_prices_product_id'), 'prices', ['product_id'], unique=False)
    op.add_column('products_to_categories', sa.Column('visible', sa.Boolean(), nullable=True))
    op.drop_column('products_to_categories', 'amount')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products_to_categories', sa.Column('amount', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('products_to_categories', 'visible')
    op.drop_index(op.f('ix_prices_product_id'), table_name='prices')
    op.drop_index(op.f('ix_prices_id'), table_name='prices')
    op.drop_table('prices')
    # ### end Alembic commands ###
