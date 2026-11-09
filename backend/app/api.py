from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.models import Assessment, AssessmentResult, Attempt, Concept, Course, Diagnosis, Intervention, LearningEvent, Mastery, MasteryHistory, Problem, SkillMastery, SkillMasteryHistory, Student, TutorInteraction
from app.schemas import AssessmentSubmit, AttemptOut, ConceptDetail, ConceptOut, CourseOut, DiagnosisRequest, EventCreate, InterventionRequest, MasteryOut, ProblemOut, StudentCreate, StudentOut, SubmissionCreate, TutorRequest
from app.services.bkt import update
from app.services.diagnosis import diagnose
from app.services.interventions import select_intervention
from app.services.judge0 import Judge0Service, JudgeUnavailable
from app.intelligence.bkt import parameters_for,update_probability
from app.intelligence.tutor import generate_tutor_response
from app.intelligence.diagnosis import canonical_category

router = APIRouter(prefix="/api/v1")

def need(db, cls, ident):
    obj = db.get(cls, ident)
    if not obj: raise HTTPException(404, f"{cls.__name__} not found")
    return obj

def ensure_student_skills(db:Session,student:Student):
    existing=set(db.scalars(select(SkillMastery.skill_key).where(SkillMastery.student_id==student.id)).all())
    for concept in db.scalars(select(Concept)):
        key=f"{concept.slug}:core"
        if key not in existing:
            params=parameters_for(key);db.add(SkillMastery(student_id=student.id,concept_id=concept.id,skill_key=key,probability=params.initial,mastery_threshold=params.threshold))

@router.post("/students", response_model=StudentOut, status_code=201)
def create_student(body: StudentCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(Student).where(Student.email == body.email))
    if existing:
        ensure_student_skills(db,existing);db.commit();return existing
    student = Student(**body.model_dump()); db.add(student); db.flush()
    for concept in db.scalars(select(Concept)):
        db.add(Mastery(student_id=student.id, concept_id=concept.id, probability=.2))
        params=parameters_for(f"{concept.slug}:core")
        db.add(SkillMastery(student_id=student.id,concept_id=concept.id,skill_key=f"{concept.slug}:core",probability=params.initial,mastery_threshold=params.threshold))
    db.commit(); db.refresh(student); return student

@router.get("/students/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)): return need(db, Student, student_id)

@router.get("/students/{student_id}/profile")
def profile(student_id: int, db: Session = Depends(get_db)):
    student = need(db, Student, student_id)
    return {"student": StudentOut.model_validate(student), "attempts": db.scalar(select(func.count()).select_from(Attempt).where(Attempt.student_id == student_id)), "events": db.scalar(select(func.count()).select_from(LearningEvent).where(LearningEvent.student_id == student_id))}

@router.get("/courses", response_model=list[CourseOut])
def courses(db: Session = Depends(get_db)): return db.scalars(select(Course)).all()

@router.get("/courses/{course_id}/concepts", response_model=list[ConceptOut])
def concepts(course_id: int, db: Session = Depends(get_db)):
    need(db, Course, course_id); return db.scalars(select(Concept).where(Concept.course_id == course_id).order_by(Concept.position)).all()

@router.get("/concepts/{concept_id}", response_model=ConceptDetail)
def concept(concept_id: int, db: Session = Depends(get_db)): return need(db, Concept, concept_id)

@router.get("/concepts/{concept_id}/lesson", response_model=ConceptDetail)
def lesson(concept_id: int, student_id: int | None = None, db: Session = Depends(get_db)):
    item = need(db, Concept, concept_id)
    if student_id:
        need(db, Student, student_id); db.add(LearningEvent(student_id=student_id, concept_id=concept_id, kind="lesson_opened")); db.commit()
    return item

@router.get("/problems", response_model=list[ProblemOut])
def problems(concept_id: int | None = None, db: Session = Depends(get_db)):
    query = select(Problem)
    if concept_id: query = query.where(Problem.concept_id == concept_id)
    return db.scalars(query).all()

@router.get("/students/{student_id}/mastery", response_model=list[MasteryOut])
def mastery(student_id: int, db: Session = Depends(get_db)):
    need(db, Student, student_id); return db.scalars(select(Mastery).where(Mastery.student_id == student_id)).all()

@router.get("/concepts/{concept_id}/mastery")
def concept_mastery(concept_id: int, student_id: int = Query(...), db: Session = Depends(get_db)):
    item = db.scalar(select(Mastery).where(Mastery.student_id == student_id, Mastery.concept_id == concept_id))
    if not item: raise HTTPException(404, "Mastery estimate not found")
    return {"concept_id": concept_id, "student_id": student_id, "estimate": item.probability, "observations": item.observations}

@router.get("/students/{student_id}/dashboard")
def dashboard(student_id: int, db: Session = Depends(get_db)):
    need(db, Student, student_id)
    rows = db.execute(select(Mastery, Concept).join(Concept, Concept.id == Mastery.concept_id).where(Mastery.student_id == student_id)).all()
    concepts = [{"id": c.id, "title": c.title, "probability": m.probability, "observations": m.observations} for m, c in rows]
    attempts = db.scalars(select(Attempt).where(Attempt.student_id == student_id).order_by(Attempt.id.desc()).limit(8)).all()
    evaluated = [a for a in attempts if a.correct is not None]
    skill_rows=db.scalars(select(SkillMastery).where(SkillMastery.student_id==student_id)).all()
    recent_diagnoses=db.execute(select(Diagnosis,Concept).join(Attempt,Attempt.id==Diagnosis.attempt_id).join(Concept,Concept.id==Diagnosis.concept_id).where(Attempt.student_id==student_id).order_by(Diagnosis.id.desc()).limit(4)).all()
    return {"mastery": concepts, "overall": sum(x["probability"] for x in concepts) / max(len(concepts), 1), "accuracy": sum(bool(a.correct) for a in evaluated) / max(len(evaluated), 1), "recent_attempts": [AttemptOut.model_validate(a) for a in attempts], "recommended_next": min(concepts, key=lambda x: x["probability"]) if concepts else None,"intelligence":{"skills_tracked":len(skill_rows),"skills_mastered":sum(row.probability>=row.mastery_threshold for row in skill_rows),"recent_diagnoses":[{"category":d.category,"title":d.title,"severity":d.severity,"concept":c.title,"confidence":d.confidence} for d,c in recent_diagnoses]}}

@router.post("/events", status_code=201)
def event(body: EventCreate, db: Session = Depends(get_db)):
    need(db, Student, body.student_id); item = LearningEvent(**body.model_dump()); db.add(item); db.commit(); return {"id": item.id}

@router.post("/submissions", response_model=AttemptOut, status_code=202)
def submit(body: SubmissionCreate, tasks: BackgroundTasks, db: Session = Depends(get_db)):
    need(db, Student, body.student_id); need(db, Problem, body.problem_id)
    attempt = Attempt(**body.model_dump(), status="QUEUED"); db.add(attempt); db.add(LearningEvent(student_id=body.student_id, kind="code_submitted", payload={"problem_id": body.problem_id})); db.commit(); db.refresh(attempt)
    tasks.add_task(evaluate_attempt, attempt.id); return attempt

async def evaluate_attempt(attempt_id: int):
    with SessionLocal() as db:
        attempt = need(db, Attempt, attempt_id); problem = need(db, Problem, attempt.problem_id); attempt.status = "RUNNING"; db.commit()
        try:
            result = await Judge0Service().evaluate(attempt.source_code, problem.visible_cases + problem.hidden_cases)
            attempt.status = "EVALUATED"; attempt.correct = result["correct"]; attempt.compiler_output = result["compiler_output"]; attempt.runtime_ms = result["runtime_ms"]; attempt.memory_kb = result["memory_kb"]
            attempt.results = [{k: v for k, v in r.items() if k != "input" or v is not None} for r in result["results"]]; db.flush()
            mastery_row = db.scalar(select(Mastery).where(Mastery.student_id == attempt.student_id, Mastery.concept_id == problem.concept_id))
            before = mastery_row.probability; after = update(before, bool(attempt.correct)); mastery_row.probability = after; mastery_row.observations += 1
            db.add(MasteryHistory(mastery_id=mastery_row.id, attempt_id=attempt.id, before=before, after=after, correct=bool(attempt.correct)))
            core_skill=_update_skill_mastery(db,attempt.student_id,problem,f"{need(db,Concept,problem.concept_id).slug}:core",bool(attempt.correct),attempt.id)
            diagnosis_row = None
            if not attempt.correct:
                d = diagnose(attempt, problem); diagnosis_row = Diagnosis(attempt_id=attempt.id, concept_id=problem.concept_id, **d); db.add(diagnosis_row); db.flush()
                _update_skill_mastery(db,attempt.student_id,problem,f"{need(db,Concept,problem.concept_id).slug}:{diagnosis_row.category}",False,attempt.id)
            policy = select_intervention(db, attempt.student_id, problem.concept_id, diagnosis_row)
            db.add(Intervention(student_id=attempt.student_id, concept_id=problem.concept_id, diagnosis_id=diagnosis_row.id if diagnosis_row else None, **policy))
            db.add(LearningEvent(student_id=attempt.student_id, concept_id=problem.concept_id, kind="submission_evaluated", payload={"attempt_id": attempt.id, "correct": attempt.correct, "mastery_before": before, "mastery_after": after,"skill_mastery_after":core_skill.probability,"diagnosis":diagnosis_row.category if diagnosis_row else None})); attempt.status = "COMPLETED"; db.commit()
        except JudgeUnavailable as exc:
            attempt.status = "FAILED"; attempt.compiler_output = str(exc); db.commit()

@router.get("/submissions/{attempt_id}", response_model=AttemptOut)
def submission(attempt_id: int, db: Session = Depends(get_db)): return need(db, Attempt, attempt_id)

def _update_skill_mastery(db:Session,student_id:int,problem:Problem,skill_key:str,correct:bool,attempt_id:int)->SkillMastery:
    params=parameters_for(skill_key)
    row=db.scalar(select(SkillMastery).where(SkillMastery.student_id==student_id,SkillMastery.concept_id==problem.concept_id,SkillMastery.skill_key==skill_key))
    if not row:
        row=SkillMastery(student_id=student_id,concept_id=problem.concept_id,skill_key=skill_key,probability=params.initial,mastery_threshold=params.threshold);db.add(row);db.flush()
    result=update_probability(row.probability,correct,params)
    row.probability=result.updated_probability;row.observations+=1
    db.add(SkillMasteryHistory(skill_mastery_id=row.id,attempt_id=attempt_id,prior_probability=result.prior_probability,posterior_probability=result.posterior_probability,updated_probability=result.updated_probability,correct=correct))
    return row

@router.get("/submissions/{attempt_id}/insights")
def submission_insights(attempt_id:int,db:Session=Depends(get_db)):
    attempt=need(db,Attempt,attempt_id);problem=need(db,Problem,attempt.problem_id);concept=need(db,Concept,problem.concept_id)
    diagnosis_row=db.scalar(select(Diagnosis).where(Diagnosis.attempt_id==attempt_id))
    intervention_row=db.scalar(select(Intervention).where(Intervention.student_id==attempt.student_id,Intervention.concept_id==problem.concept_id).order_by(Intervention.id.desc()))
    concept_mastery=db.scalar(select(Mastery).where(Mastery.student_id==attempt.student_id,Mastery.concept_id==problem.concept_id))
    skills=db.scalars(select(SkillMastery).where(SkillMastery.student_id==attempt.student_id,SkillMastery.concept_id==problem.concept_id)).all()
    diagnosis_data=None if not diagnosis_row else {"id":diagnosis_row.id,"category":diagnosis_row.category,"title":diagnosis_row.title,"severity":diagnosis_row.severity,"confidence":diagnosis_row.confidence,"explanation":diagnosis_row.explanation,"evidence":diagnosis_row.evidence,"suggested_action":diagnosis_row.suggested_action,"misconception":diagnosis_row.misconception,"details":diagnosis_row.details}
    intervention_data=None if not intervention_row else {"id":intervention_row.id,"kind":intervention_row.kind,"scaffold_level":intervention_row.scaffold_level,"priority":intervention_row.priority,"rationale":intervention_row.rationale,"recommended_mode":"visualise" if intervention_row.kind=="Visualization" else "code"}
    return {"attempt_id":attempt_id,"concept":{"id":concept.id,"title":concept.title,"visualizer":concept.visualizer},"diagnosis":diagnosis_data,"intervention":intervention_data,"mastery":{"probability":concept_mastery.probability,"observations":concept_mastery.observations},"skills":[{"key":row.skill_key,"probability":row.probability,"observations":row.observations,"mastered":row.probability>=row.mastery_threshold} for row in skills]}

@router.post("/diagnosis")
def diagnosis(body: DiagnosisRequest, db: Session = Depends(get_db)):
    attempt = need(db, Attempt, body.attempt_id)
    existing = db.scalar(select(Diagnosis).where(Diagnosis.attempt_id == attempt.id))
    if existing: return existing
    if attempt.correct is None: raise HTTPException(409, "Attempt has not been evaluated")
    problem = need(db, Problem, attempt.problem_id); row = Diagnosis(attempt_id=attempt.id, concept_id=problem.concept_id, **diagnose(attempt, problem)); db.add(row); db.commit(); db.refresh(row); return row

@router.post("/interventions/next")
def intervention(body: InterventionRequest, db: Session = Depends(get_db)):
    diagnosis_row = need(db, Diagnosis, body.diagnosis_id) if body.diagnosis_id else None
    policy = select_intervention(db, body.student_id, body.concept_id, diagnosis_row); row = Intervention(student_id=body.student_id, concept_id=body.concept_id, diagnosis_id=body.diagnosis_id, **policy); db.add(row); db.commit(); db.refresh(row); return row

@router.get("/students/{student_id}/learning-history")
def history(student_id: int, db: Session = Depends(get_db)):
    need(db, Student, student_id); return db.scalars(select(LearningEvent).where(LearningEvent.student_id == student_id).order_by(LearningEvent.id.desc()).limit(100)).all()

async def _tutor(body: TutorRequest, db: Session,response_type:str="hint"):
    concept = need(db, Concept, body.concept_id)
    mastery_row = db.scalar(select(Mastery).where(Mastery.student_id == body.student_id, Mastery.concept_id == body.concept_id))
    intervention_row = need(db, Intervention, body.intervention_id) if body.intervention_id else db.scalar(select(Intervention).where(Intervention.student_id == body.student_id, Intervention.concept_id == body.concept_id).order_by(Intervention.id.desc()))
    diagnosis_row = db.get(Diagnosis, intervention_row.diagnosis_id) if intervention_row and intervention_row.diagnosis_id else None
    recent_attempt=db.scalar(select(Attempt).join(Problem,Problem.id==Attempt.problem_id).where(Attempt.student_id==body.student_id,Problem.concept_id==body.concept_id).order_by(Attempt.id.desc()))
    context = {"concept": concept.title, "mastery_estimate": round(mastery_row.probability, 3) if mastery_row else .2, "diagnosis": canonical_category(diagnosis_row.category) if diagnosis_row else "none", "diagnostic_explanation":diagnosis_row.explanation if diagnosis_row else "none", "intervention": intervention_row.kind if intervention_row else "conceptual hint", "scaffold_level": intervention_row.scaffold_level if intervention_row else 1, "student_question": body.question or "Provide the next helpful prompt.","recent_attempt_status":recent_attempt.status if recent_attempt else "none","student_code":recent_attempt.source_code[:6000] if recent_attempt else "not provided","compiler_or_runtime_feedback":(recent_attempt.compiler_output or "none")[:2000] if recent_attempt else "none"}
    result=await generate_tutor_response(context,response_type)
    db.add(TutorInteraction(student_id=body.student_id,concept_id=body.concept_id,intervention_id=intervention_row.id if intervention_row else None,response_type=result.response_type,provider=result.provider,model=result.model,fallback=result.fallback,prompt_context=context,response=result.response))
    db.add(LearningEvent(student_id=body.student_id, concept_id=body.concept_id, kind="hint_viewed", payload={"fallback": result.fallback, "scaffold_level": context["scaffold_level"],"provider":result.provider,"model":result.model})); db.commit()
    return {"response": result.response, "fallback": result.fallback,"provider":result.provider,"model":result.model,"response_type":result.response_type, "context": context}

@router.post("/tutor/hints")
async def hint(body: TutorRequest, db: Session = Depends(get_db)): return await _tutor(body, db,"hint")
@router.post("/tutor/explanations")
async def explanation(body: TutorRequest, db: Session = Depends(get_db)): return await _tutor(body, db,"explanation")
@router.post("/tutor/questions")
async def question(body: TutorRequest, db: Session = Depends(get_db)): return await _tutor(body, db,"step_by_step")

@router.get("/students/{student_id}/intelligence")
def student_intelligence(student_id:int,db:Session=Depends(get_db)):
    need(db,Student,student_id)
    skills=db.execute(select(SkillMastery,Concept).join(Concept,Concept.id==SkillMastery.concept_id).where(SkillMastery.student_id==student_id).order_by(SkillMastery.probability)).all()
    diagnoses=db.execute(select(Diagnosis,Concept).join(Attempt,Attempt.id==Diagnosis.attempt_id).join(Concept,Concept.id==Diagnosis.concept_id).where(Attempt.student_id==student_id).order_by(Diagnosis.id.desc()).limit(20)).all()
    interventions=db.execute(select(Intervention,Concept).join(Concept,Concept.id==Intervention.concept_id).where(Intervention.student_id==student_id).order_by(Intervention.id.desc()).limit(20)).all()
    tutor_rows=db.execute(select(TutorInteraction,Concept).join(Concept,Concept.id==TutorInteraction.concept_id).where(TutorInteraction.student_id==student_id).order_by(TutorInteraction.id.desc()).limit(10)).all()
    events=db.scalars(select(LearningEvent).where(LearningEvent.student_id==student_id,LearningEvent.kind=="submission_evaluated").order_by(LearningEvent.id.desc()).limit(12)).all()
    return {"skills":[{"key":s.skill_key,"concept":c.title,"concept_id":c.id,"probability":s.probability,"observations":s.observations,"mastered":s.probability>=s.mastery_threshold} for s,c in skills],"diagnoses":[{"category":canonical_category(d.category),"title":d.title,"severity":d.severity,"concept":c.title,"confidence":d.confidence,"created_from_attempt":d.attempt_id} for d,c in diagnoses],"interventions":[{"kind":item.kind,"level":item.scaffold_level,"priority":item.priority,"rationale":item.rationale,"concept":concept.title,"created_at":item.created_at} for item,concept in interventions],"tutor_activity":[{"provider":item.provider,"model":item.model,"fallback":item.fallback,"response_type":item.response_type,"concept":concept.title,"created_at":item.created_at} for item,concept in tutor_rows],"mastery_movements":[event.payload for event in events]}

@router.get("/system/intelligence-status")
def intelligence_status(db:Session=Depends(get_db)):
    last_tutor=db.scalar(select(TutorInteraction).order_by(TutorInteraction.id.desc()))
    return {"pipeline":"active","models":[
        {"id":"bkt","name":"Bayesian Knowledge Tracing","type":"probabilistic","status":"active","detail":"Persistent concept and skill mastery","version":"BKT v2"},
        {"id":"diagnosis","name":"Programming Error Diagnoser","type":"rule-based","status":"active","detail":"Java compiler, runtime, boundary and misconception signals","version":"9 categories"},
        {"id":"intervention","name":"Reinforcement Selector","type":"policy","status":"active","detail":"Mastery + diagnosis + repeated-error routing","version":"6 scaffold levels"},
        {"id":"tutor","name":"Local Qwen Tutor","type":"generative","status":"active" if last_tutor and not last_tutor.fallback else "ready","detail":"Last response used local Ollama" if last_tutor and not last_tutor.fallback else "Local provider configured; deterministic fallback available","version":last_tutor.model if last_tutor else settings.ollama_model},
    ],"totals":{"skill_states":db.scalar(select(func.count()).select_from(SkillMastery)) or 0,"diagnoses":db.scalar(select(func.count()).select_from(Diagnosis)) or 0,"interventions":db.scalar(select(func.count()).select_from(Intervention)) or 0,"tutor_responses":db.scalar(select(func.count()).select_from(TutorInteraction)) or 0}}

@router.get("/analytics/intelligence")
def intelligence_analytics(db:Session=Depends(get_db)):
    category_rows=db.execute(select(Diagnosis.category,func.count()).group_by(Diagnosis.category).order_by(func.count().desc())).all()
    category_totals={}
    for category,count in category_rows:
        key=canonical_category(category);category_totals[key]=category_totals.get(key,0)+count
    interventions=db.execute(select(Intervention.kind,func.count()).group_by(Intervention.kind).order_by(func.count().desc())).all()
    struggling=db.execute(select(SkillMastery,Student,Concept).join(Student,Student.id==SkillMastery.student_id).join(Concept,Concept.id==SkillMastery.concept_id).where(SkillMastery.observations>0,SkillMastery.probability<.4).order_by(SkillMastery.probability).limit(20)).all()
    return {"diagnosis_counts":[{"category":category,"count":count} for category,count in sorted(category_totals.items(),key=lambda item:item[1],reverse=True)],"intervention_counts":[{"kind":kind,"count":count} for kind,count in interventions],"struggling_skills":[{"student_id":student.id,"student":student.name,"concept":concept.title,"skill":skill.skill_key,"probability":skill.probability} for skill,student,concept in struggling]}

@router.get("/assessments")
def assessments(db: Session = Depends(get_db)): return db.scalars(select(Assessment)).all()

@router.post("/assessments/{assessment_id}/submit")
def submit_assessment(assessment_id: int, body: AssessmentSubmit, db: Session = Depends(get_db)):
    assessment = need(db, Assessment, assessment_id); attempts = db.scalars(select(Attempt).where(Attempt.id.in_(body.attempt_ids), Attempt.student_id == body.student_id, Attempt.assisted.is_(False), Attempt.status == "COMPLETED")).all()
    allowed = set(assessment.problem_ids); valid = [a for a in attempts if a.problem_id in allowed]
    if not valid: raise HTTPException(422, "No completed independent attempts supplied")
    performance = {}; correct = 0
    for attempt in valid:
        problem = need(db, Problem, attempt.problem_id); performance.setdefault(str(problem.concept_id), {"correct": 0, "total": 0}); performance[str(problem.concept_id)]["total"] += 1
        if attempt.correct: performance[str(problem.concept_id)]["correct"] += 1; correct += 1
    row = AssessmentResult(assessment_id=assessment_id, student_id=body.student_id, score=100 * correct / len(valid), concept_performance=performance); db.add(row); db.add(LearningEvent(student_id=body.student_id, kind="assessment_completed", payload={"assessment_id": assessment_id, "score": row.score})); db.commit(); return row
