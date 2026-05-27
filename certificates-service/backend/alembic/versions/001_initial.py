"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="manager"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # products
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("normalized_name", sa.String(500), nullable=False),
        sa.Column("product_type", sa.String(100), nullable=True),
        sa.Column("aliases", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # certificates
    op.create_table(
        "certificates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("preview_path", sa.String(1000), nullable=True),
        sa.Column("file_type", sa.String(100), nullable=True),
        sa.Column("file_hash", sa.String(64), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column("certificate_number", sa.String(200), nullable=True),
        sa.Column("certificate_date", sa.Date(), nullable=True),
        sa.Column("manufacturer", sa.String(500), nullable=True),
        sa.Column("supplier", sa.String(500), nullable=True),
        sa.Column("product_name", sa.String(1000), nullable=True),
        sa.Column("normalized_product_name", sa.String(1000), nullable=True),
        sa.Column("product_type", sa.String(200), nullable=True),
        sa.Column("material", sa.String(200), nullable=True),
        sa.Column("gost", sa.String(200), nullable=True),
        sa.Column("dimensions", sa.String(200), nullable=True),
        sa.Column("batch_number", sa.String(200), nullable=True),
        sa.Column("heat_number", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="uploaded"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_certificates_file_hash", "certificates", ["file_hash"])
    op.create_index("ix_certificates_status", "certificates", ["status"])
    op.create_index("ix_certificates_product_type", "certificates", ["product_type"])
    op.create_index("ix_certificates_material", "certificates", ["material"])
    op.create_index("ix_certificates_certificate_date", "certificates", ["certificate_date"])

    # Full-text search index (Russian + English)
    op.execute("""
        CREATE INDEX ix_certificates_fts ON certificates
        USING gin(
            to_tsvector('russian',
                coalesce(normalized_product_name, '') || ' ' ||
                coalesce(extracted_text, '') || ' ' ||
                coalesce(manufacturer, '') || ' ' ||
                coalesce(gost, '') || ' ' ||
                coalesce(material, '') || ' ' ||
                coalesce(certificate_number, '') || ' ' ||
                coalesce(dimensions, '')
            )
        )
    """)

    # Trigram index for fuzzy search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("""
        CREATE INDEX ix_certificates_trgm ON certificates
        USING gin(normalized_product_name gin_trgm_ops)
    """)

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.String(100), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("certificates")
    op.drop_table("products")
    op.drop_table("users")
