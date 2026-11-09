from dataclasses import dataclass
from app.intelligence.bkt import SkillParameters,update_probability

@dataclass(frozen=True)
class BKTParameters:
    initial:float=.2
    transition:float=.1
    guess:float=.2
    slip:float=.1

def update(prior:float,correct:bool,params:BKTParameters|SkillParameters|None=None)->float:
    if params is None: params=BKTParameters()
    if isinstance(params,BKTParameters):
        params=SkillParameters(initial=params.initial,learn=params.transition,guess=params.guess,slip=params.slip)
    return update_probability(prior,correct,params).updated_probability
