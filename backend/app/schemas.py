from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class ORM(BaseModel): model_config = ConfigDict(from_attributes=True)
class StudentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
class StudentOut(ORM):
    id: int; name: str; email: str; created_at: datetime
class CourseOut(ORM):
    id: int; slug: str; title: str; description: str
class ConceptOut(ORM):
    id: int; course_id: int; slug: str; title: str; summary: str; prerequisites: list; position: int; visualizer: str
class ConceptDetail(ConceptOut):
    explanation: str; complexity: dict; examples: list
class ProblemOut(ORM):
    id: int; concept_id: int; title: str; statement: str; difficulty: str; starter_code: str; visible_cases: list
class MasteryOut(ORM):
    concept_id: int; probability: float; observations: int; updated_at: datetime
class EventCreate(BaseModel):
    student_id: int; concept_id: int | None = None; kind: str; payload: dict = {}
class SubmissionCreate(BaseModel):
    student_id: int; problem_id: int; source_code: str = Field(min_length=10, max_length=50000); assisted: bool = False
class AttemptOut(ORM):
    id: int; student_id: int; problem_id: int; status: str; correct: bool | None; compiler_output: str | None; runtime_ms: float | None; memory_kb: int | None; results: list; created_at: datetime
class DiagnosisRequest(BaseModel): attempt_id: int
class InterventionRequest(BaseModel): student_id: int; concept_id: int; diagnosis_id: int | None = None
class TutorRequest(BaseModel): student_id: int; concept_id: int; problem_id: int | None = None; intervention_id: int | None = None; question: str | None = None
class AssessmentSubmit(BaseModel): student_id: int; attempt_ids: list[int]
