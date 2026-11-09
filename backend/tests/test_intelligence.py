from app.models import Attempt, Mastery, Problem, Student
from app.services.diagnosis import diagnose,diagnose_all
from app.services.interventions import select_intervention
from app.intelligence.bkt import parameters_for,update_probability
from app.intelligence.intervention import choose_intervention

def test_diagnoses_compiler_signal(db):
    p=db.query(Problem).first(); a=Attempt(student_id=1,problem_id=p.id,source_code='bad code here',status='COMPLETED',correct=False,compiler_output="error: ';' expected",results=[])
    result=diagnose(a,p); assert result['category']=='compilation_error'; assert result['confidence']>.9; assert result['severity']=='high'

def test_multiple_java_errors_are_preserved(db):
    p=db.query(Problem).first();a=Attempt(student_id=1,problem_id=p.id,source_code='bad code here',status='COMPLETED',correct=False,compiler_output='EmptyStackException\nNullPointerException',results=[])
    categories={item['category'] for item in diagnose_all(a,p)}
    assert {'stack_underflow','null_pointer_error'}<=categories

def test_skill_bkt_returns_persistable_details():
    params=parameters_for('stacks:stack_underflow');result=update_probability(params.initial,False,params)
    assert result.posterior_probability<result.prior_probability
    assert 0<=result.updated_probability<=1

def test_repeated_errors_escalate_to_worked_example():
    decision=choose_intervention(.7,'logical_error',3)
    assert decision.kind=='Worked example';assert decision.scaffold_level==5;assert decision.priority=='high'

def test_policy_recommends_independent_work_for_high_mastery(db):
    s=Student(name='Grace',email='grace@example.com'); db.add(s); db.flush(); p=db.query(Problem).first(); db.add(Mastery(student_id=s.id,concept_id=p.concept_id,probability=.9)); db.commit()
    result=select_intervention(db,s.id,p.concept_id); assert result['scaffold_level']==0; assert result['kind']=='Independent practice'
