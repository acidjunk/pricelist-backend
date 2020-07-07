"""empty message

Revision ID: 338e6fa88d5e
Revises: c7430c5fca52
Create Date: 2020-07-07 17:30:27.219332

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "338e6fa88d5e"
down_revision = "c7430c5fca52"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("short_description_nl", sa.String(), nullable=True),
        sa.Column("description_nl", sa.String(), nullable=True),
        sa.Column("short_description_en", sa.String(), nullable=True),
        sa.Column("description_en", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("modified_at", sa.DateTime(), nullable=True),
        sa.Column("complete", sa.Boolean(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("disapproved_reason", sa.String(), nullable=True),
        sa.Column("image_1", sa.String(length=255), nullable=True),
        sa.Column("image_2", sa.String(length=255), nullable=True),
        sa.Column("image_3", sa.String(length=255), nullable=True),
        sa.Column("image_4", sa.String(length=255), nullable=True),
        sa.Column("image_5", sa.String(length=255), nullable=True),
        sa.Column("image_6", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["approved_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_products_id"), "products", ["id"], unique=False)
    op.create_index(op.f("ix_products_image_1"), "products", ["image_1"], unique=True)
    op.create_index(op.f("ix_products_image_2"), "products", ["image_2"], unique=True)
    op.create_index(op.f("ix_products_image_3"), "products", ["image_3"], unique=True)
    op.create_index(op.f("ix_products_image_4"), "products", ["image_4"], unique=True)
    op.create_index(op.f("ix_products_image_5"), "products", ["image_5"], unique=True)
    op.create_index(op.f("ix_products_image_6"), "products", ["image_6"], unique=True)
    op.create_index(op.f("ix_products_name"), "products", ["name"], unique=True)
    op.create_table(
        "kinds_to_strains",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("strain_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["kind_id"], ["kinds.id"]),
        sa.ForeignKeyConstraint(["strain_id"], ["strains.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_kinds_to_strains_id"), "kinds_to_strains", ["id"], unique=False)
    op.create_index(op.f("ix_kinds_to_strains_kind_id"), "kinds_to_strains", ["kind_id"], unique=False)
    op.create_index(op.f("ix_kinds_to_strains_strain_id"), "kinds_to_strains", ["strain_id"], unique=False)
    op.add_column("kinds", sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("kinds", sa.Column("disapproved_reason", sa.String(), nullable=True))
    op.drop_index("ix_kinds_strain1_id", table_name="kinds")
    op.drop_index("ix_kinds_strain2_id", table_name="kinds")
    op.drop_constraint("kinds_strain2_id_fkey", "kinds", type_="foreignkey")
    op.drop_constraint("kinds_strain1_id_fkey", "kinds", type_="foreignkey")
    op.create_foreign_key(None, "kinds", "user", ["approved_by"], ["id"])
    op.drop_column("kinds", "strain1_id")
    op.drop_column("kinds", "strain2_id")
    op.add_column("shops_to_price", sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f("ix_shops_to_price_product_id"), "shops_to_price", ["product_id"], unique=False)
    op.create_foreign_key(None, "shops_to_price", "products", ["product_id"], ["id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "shops_to_price", type_="foreignkey")
    op.drop_index(op.f("ix_shops_to_price_product_id"), table_name="shops_to_price")
    op.drop_column("shops_to_price", "product_id")
    op.add_column("kinds", sa.Column("strain2_id", postgresql.UUID(), autoincrement=False, nullable=True))
    op.add_column("kinds", sa.Column("strain1_id", postgresql.UUID(), autoincrement=False, nullable=True))
    op.drop_constraint(None, "kinds", type_="foreignkey")
    op.create_foreign_key("kinds_strain1_id_fkey", "kinds", "strains", ["strain1_id"], ["id"])
    op.create_foreign_key("kinds_strain2_id_fkey", "kinds", "strains", ["strain2_id"], ["id"])
    op.create_index("ix_kinds_strain2_id", "kinds", ["strain2_id"], unique=False)
    op.create_index("ix_kinds_strain1_id", "kinds", ["strain1_id"], unique=False)
    op.drop_column("kinds", "disapproved_reason")
    op.drop_column("kinds", "approved_by")
    op.drop_index(op.f("ix_kinds_to_strains_strain_id"), table_name="kinds_to_strains")
    op.drop_index(op.f("ix_kinds_to_strains_kind_id"), table_name="kinds_to_strains")
    op.drop_index(op.f("ix_kinds_to_strains_id"), table_name="kinds_to_strains")
    op.drop_table("kinds_to_strains")
    op.drop_index(op.f("ix_products_name"), table_name="products")
    op.drop_index(op.f("ix_products_image_6"), table_name="products")
    op.drop_index(op.f("ix_products_image_5"), table_name="products")
    op.drop_index(op.f("ix_products_image_4"), table_name="products")
    op.drop_index(op.f("ix_products_image_3"), table_name="products")
    op.drop_index(op.f("ix_products_image_2"), table_name="products")
    op.drop_index(op.f("ix_products_image_1"), table_name="products")
    op.drop_index(op.f("ix_products_id"), table_name="products")
    op.drop_table("products")
    # ### end Alembic commands ###
