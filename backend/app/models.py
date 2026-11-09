from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

def now(): return datetime.now(timezone.utc)

class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    concepts = relationship("Concept", back_populates="course", order_by="Concept.position")

class Concept(Base):
    __tablename__ = "concepts"
    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    complexity: Mapped[dict] = mapped_column(JSON, default=dict)
    examples: Mapped[list] = mapped_column(JSON, default=list)
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)
    visualizer: Mapped[str] = mapped_column(String(40), default="array")
    position: Mapped[int] = mapped_column(Integer)
    course = relationship("Course", back_populates="concepts")

class Problem(Base):
    __tablename__ = "problems"
    id: Mapped[int] = mapped_column(primary_key=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    statement: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20))
    starter_code: Mapped[str] = mapped_column(Text)
    visible_cases: Mapped[list] = mapped_column(JSON, default=list)
    hidden_cases: Mapped[list] = mapped_column(JSON, default=list)

class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    source_code: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(20), default="java")
    status: Mapped[str] = mapped_column(String(20), default="CREATED")
    correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    assisted: Mapped[bool] = mapped_column(Boolean, default=False)
    judge_token: Mapped[str | None] = mapped_column(String(100), nullable=True)
    compiler_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    runtime_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    results: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Mastery(Base):
    __tablename__ = "mastery"
    __table_args__ = (UniqueConstraint("student_id", "concept_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), index=True)
    probability: Mapped[float] = mapped_column(Float, default=.2)
    observations: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

class MasteryHistory(Base):
    __tablename__ = "mastery_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    mastery_id: Mapped[int] = mapped_column(ForeignKey("mastery.id"))
    attempt_id: Mapped[int | None] = mapped_column(ForeignKey("attempts.id"), nullable=True)
    before: Mapped[float] = mapped_column(Float)
    after: Mapped[float] = mapped_column(Float)
    correct: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class SkillMastery(Base):
    __tablename__ = "skill_mastery"
    __table_args__ = (UniqueConstraint("student_id", "concept_id", "skill_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), index=True)
    skill_key: Mapped[str] = mapped_column(String(120), index=True)
    probability: Mapped[float] = mapped_column(Float, default=.2)
    observations: Mapped[int] = mapped_column(Integer, default=0)
    mastery_threshold: Mapped[float] = mapped_column(Float, default=.85)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

class SkillMasteryHistory(Base):
    __tablename__ = "skill_mastery_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    skill_mastery_id: Mapped[int] = mapped_column(ForeignKey("skill_mastery.id"), index=True)
    attempt_id: Mapped[int | None] = mapped_column(ForeignKey("attempts.id"), nullable=True)
    prior_probability: Mapped[float] = mapped_column(Float)
    posterior_probability: Mapped[float] = mapped_column(Float)
    updated_probability: Mapped[float] = mapped_column(Float)
    correct: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Diagnosis(Base):
    __tablename__ = "diagnoses"
    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id"), unique=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"))
    category: Mapped[str] = mapped_column(String(80))
    evidence: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    recommended_response: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    title: Mapped[str] = mapped_column(String(160), default="Learning diagnosis")
    explanation: Mapped[str] = mapped_column(Text, default="")
    suggested_action: Mapped[str] = mapped_column(Text, default="")
    misconception: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[list] = mapped_column(JSON, default=list)

class Intervention(Base):
    __tablename__ = "interventions"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"))
    diagnosis_id: Mapped[int | None] = mapped_column(ForeignKey("diagnoses.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(80))
    scaffold_level: Mapped[int] = mapped_column(Integer)
    rationale: Mapped[str] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class LearningEvent(Base):
    __tablename__ = "learning_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    concept_id: Mapped[int | None] = mapped_column(ForeignKey("concepts.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(60), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class TutorInteraction(Base):
    __tablename__ = "tutor_interactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), index=True)
    intervention_id: Mapped[int | None] = mapped_column(ForeignKey("interventions.id"), nullable=True)
    response_type: Mapped[str] = mapped_column(String(40))
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(120))
    fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    prompt_context: Mapped[dict] = mapped_column(JSON, default=dict)
    response: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(30), default="topic")
    difficulty: Mapped[str] = mapped_column(String(20), default="mixed")
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    problem_ids: Mapped[list] = mapped_column(JSON, default=list)

class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    concept_performance: Mapped[dict] = mapped_column(JSON, default=dict)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
