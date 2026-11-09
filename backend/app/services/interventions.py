from sqlalchemy import func,select
from sqlalchemy.orm import Session
from app.models import Attempt, Diagnosis, Intervention, Mastery
from app.intelligence.intervention import choose_intervention

def select_intervention(db: Session, student_id: int, concept_id: int, diagnosis: Diagnosis | None = None) -> dict:
    mastery = db.scalar(select(Mastery).where(Mastery.student_id == student_id, Mastery.concept_id == concept_id))
    probability = mastery.probability if mastery else .2
    previous = db.scalars(select(Intervention).where(Intervention.student_id == student_id, Intervention.concept_id == concept_id).order_by(Intervention.id.desc()).limit(3)).all()
    category = diagnosis.category if diagnosis else ""
    repeated = 0
    if category:
        repeated = db.scalar(select(func.count()).select_from(Diagnosis).join(Attempt,Attempt.id==Diagnosis.attempt_id).where(Attempt.student_id==student_id,Diagnosis.concept_id==concept_id,Diagnosis.category==category)) or 0
    decision=choose_intervention(probability,category,repeated,{item.kind for item in previous})
    return {"kind":decision.kind,"scaffold_level":decision.scaffold_level,"priority":decision.priority,"rationale":decision.rationale}
