"""persistent skill intelligence"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"

def upgrade():
    # The original baseline migration creates the complete SQLAlchemy metadata.
    # Fresh installations therefore already have these tables; retain this
    # revision as a no-op marker while supporting databases from older builds.
    if "skill_mastery" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table("skill_mastery",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("skill_key", sa.String(120), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("observations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mastery_threshold", sa.Float(), nullable=False, server_default="0.85"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "concept_id", "skill_key"),
    )
    op.create_index("ix_skill_mastery_student_id", "skill_mastery", ["student_id"])
    op.create_index("ix_skill_mastery_concept_id", "skill_mastery", ["concept_id"])
    op.create_index("ix_skill_mastery_skill_key", "skill_mastery", ["skill_key"])
    op.create_table("skill_mastery_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("skill_mastery_id", sa.Integer(), sa.ForeignKey("skill_mastery.id"), nullable=False),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("attempts.id"), nullable=True),
        sa.Column("prior_probability", sa.Float(), nullable=False),
        sa.Column("posterior_probability", sa.Float(), nullable=False),
        sa.Column("updated_probability", sa.Float(), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_skill_mastery_history_skill_mastery_id", "skill_mastery_history", ["skill_mastery_id"])
    with op.batch_alter_table("diagnoses") as batch:
        batch.add_column(sa.Column("severity", sa.String(20), nullable=False, server_default="medium"))
        batch.add_column(sa.Column("title", sa.String(160), nullable=False, server_default="Learning diagnosis"))
        batch.add_column(sa.Column("explanation", sa.Text(), nullable=False, server_default=""))
        batch.add_column(sa.Column("suggested_action", sa.Text(), nullable=False, server_default=""))
        batch.add_column(sa.Column("misconception", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("details", sa.JSON(), nullable=False, server_default="[]"))
    with op.batch_alter_table("interventions") as batch:
        batch.add_column(sa.Column("priority", sa.String(20), nullable=False, server_default="medium"))
    op.create_table("tutor_interactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("intervention_id", sa.Integer(), sa.ForeignKey("interventions.id"), nullable=True),
        sa.Column("response_type", sa.String(40), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("fallback", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("prompt_context", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tutor_interactions_student_id", "tutor_interactions", ["student_id"])
    op.create_index("ix_tutor_interactions_concept_id", "tutor_interactions", ["concept_id"])

def downgrade():
    op.drop_table("tutor_interactions")
    with op.batch_alter_table("interventions") as batch: batch.drop_column("priority")
    with op.batch_alter_table("diagnoses") as batch:
        for name in ("details", "misconception", "suggested_action", "explanation", "title", "severity"): batch.drop_column(name)
    op.drop_table("skill_mastery_history")
    op.drop_table("skill_mastery")
