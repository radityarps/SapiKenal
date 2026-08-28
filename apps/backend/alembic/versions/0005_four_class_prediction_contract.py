"""Add four-class prediction outcomes and non-cattle metadata."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Existing rows are backfilled as accepted records with a zero non-cattle score;
# new clients may persist rejected non-cattle attempts.

revision: str = "0005_four_class_prediction_contract"
down_revision: str | None = "0004_model_lifecycle_timestamps"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("detection_history") as batch_op:
        batch_op.add_column(
            sa.Column("score_healthy", sa.Float(), nullable=True, server_default="0")
        )
        batch_op.add_column(
            sa.Column("score_fmd", sa.Float(), nullable=True, server_default="0")
        )
        batch_op.add_column(
            sa.Column("score_lsd", sa.Float(), nullable=True, server_default="0")
        )
        batch_op.add_column(
            sa.Column("score_non_cattle", sa.Float(), nullable=True, server_default="0")
        )
        batch_op.add_column(
            sa.Column(
                "outcome",
                sa.String(length=16),
                nullable=True,
                server_default="accepted",
            )
        )
        batch_op.add_column(sa.Column("rejection_reason", sa.String(length=32)))

    op.execute(
        "UPDATE detection_history "
        "SET score_healthy = COALESCE(score_healthy, 0), "
        "score_fmd = COALESCE(score_fmd, 0), "
        "score_lsd = COALESCE(score_lsd, 0), "
        "score_non_cattle = COALESCE(score_non_cattle, 0), "
        "outcome = COALESCE(outcome, 'accepted')"
    )

    with op.batch_alter_table("detection_history") as batch_op:
        for column in (
            "score_healthy",
            "score_fmd",
            "score_lsd",
            "score_non_cattle",
            "outcome",
        ):
            batch_op.alter_column(
                column,
                existing_type=(
                    sa.Float() if column.startswith("score_") else sa.String(length=16)
                ),
                nullable=False,
                server_default=None,
            )

    with op.batch_alter_table("prediction_events") as batch_op:
        batch_op.add_column(
            sa.Column(
                "outcome", sa.String(length=16), nullable=True, server_default="failed"
            )
        )
        batch_op.add_column(sa.Column("predicted_class", sa.String(length=32)))
        batch_op.add_column(sa.Column("confidence", sa.Float()))
        batch_op.add_column(sa.Column("scores", sa.JSON()))

    op.execute(
        "UPDATE prediction_events "
        "SET outcome = CASE WHEN status = 'success' THEN 'accepted' ELSE 'failed' END "
        "WHERE outcome IS NULL OR outcome = 'failed'"
    )

    with op.batch_alter_table("prediction_events") as batch_op:
        batch_op.alter_column(
            "outcome",
            existing_type=sa.String(length=16),
            nullable=False,
            server_default=None,
        )


def downgrade() -> None:
    with op.batch_alter_table("prediction_events") as batch_op:
        batch_op.drop_column("scores")
        batch_op.drop_column("confidence")
        batch_op.drop_column("predicted_class")
        batch_op.drop_column("outcome")

    with op.batch_alter_table("detection_history") as batch_op:
        batch_op.drop_column("rejection_reason")
        batch_op.drop_column("outcome")
        batch_op.drop_column("score_non_cattle")
        batch_op.drop_column("score_lsd")
        batch_op.drop_column("score_fmd")
        batch_op.drop_column("score_healthy")
