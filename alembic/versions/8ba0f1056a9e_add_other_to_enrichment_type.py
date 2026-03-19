"""add_other_to_enrichment_type

Revision ID: 8ba0f1056a9e
Revises: b4304625bbb1
Create Date: 2026-03-19 10:02:35.220911

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '8ba0f1056a9e'
down_revision: Union[str, Sequence[str], None] = 'b4304625bbb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands manually adjusted for MySQL ENUM! ###
    op.execute("ALTER TABLE enrichments MODIFY COLUMN enrichment_type ENUM('SUMMARY', 'SCORING', 'RAG', 'OUTREACH', 'OTHER') NOT NULL")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands manually adjusted for MySQL ENUM! ###
    op.execute("ALTER TABLE enrichments MODIFY COLUMN enrichment_type ENUM('SUMMARY', 'SCORING', 'RAG', 'OUTREACH') NOT NULL")
    # ### end Alembic commands ###
