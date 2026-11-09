from dataclasses import dataclass

@dataclass(frozen=True)
class SkillParameters:
    initial: float=.20
    learn: float=.15
    guess: float=.15
    slip: float=.10
    threshold: float=.85

@dataclass(frozen=True)
class BKTResult:
    prior_probability: float
    posterior_probability: float
    updated_probability: float
    mastery_percentage: float
    is_mastered: bool

def parameters_for(skill_key:str)->SkillParameters:
    key=skill_key.lower()
    if "conceptual" in key or key.endswith(":core"): return SkillParameters(initial=.25,learn=.18,guess=.20,slip=.08)
    if "underflow" in key: return SkillParameters(initial=.15,learn=.20,guess=.10,slip=.10)
    if "parentheses" in key: return SkillParameters(initial=.20,learn=.14,guess=.12,slip=.10)
    return SkillParameters()

def update_probability(prior:float,correct:bool,params:SkillParameters|None=None)->BKTResult:
    if not isinstance(correct,bool): raise TypeError("correct must be boolean")
    if not 0<=prior<=1: raise ValueError("prior must be between 0 and 1")
    params=params or SkillParameters()
    numerator=prior*(1-params.slip) if correct else prior*params.slip
    denominator=numerator+(1-prior)*(params.guess if correct else 1-params.guess)
    posterior=prior if denominator==0 else numerator/denominator
    updated=posterior+(1-posterior)*params.learn
    return BKTResult(prior,posterior,updated,round(updated*100,2),updated>=params.threshold)
