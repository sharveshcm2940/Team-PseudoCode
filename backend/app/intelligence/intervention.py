from dataclasses import dataclass

@dataclass(frozen=True)
class InterventionDecision:
    kind:str
    scaffold_level:int
    priority:str
    rationale:str

VISUAL={"lifo_misconception","parentheses_validation"}
EXPLAIN={"stack_underflow","stack_overflow"}
HINT={"compilation_error","null_pointer_error","array_index_error","logical_error","boundary_condition"}

def choose_intervention(mastery:float,category:str="",repeated_errors:int=0,recent_kinds:set[str]|None=None)->InterventionDecision:
    category=category.strip().lower(); recent_kinds=recent_kinds or set()
    if repeated_errors>=3: kind,level,priority="Worked example",5,"high"
    elif category in VISUAL: kind,level,priority="Visualization",3,"high"
    elif category in EXPLAIN: kind,level,priority="Concept explanation",3,"high"
    elif category in HINT: kind,level,priority="Targeted hint",2,"medium"
    elif mastery<.40: kind,level,priority="Concept explanation",4,"high"
    elif mastery<.70: kind,level,priority="Guided trace",3,"medium"
    elif mastery<.85: kind,level,priority="Independent practice",1,"medium"
    else: kind,level,priority="Independent practice",0,"low"
    if kind in recent_kinds and repeated_errors<3 and level not in {0,5}:
        kind="Guided trace" if kind!="Guided trace" else "Visualization";level=3
    return InterventionDecision(kind,level,priority,f"{mastery:.0%} mastery; {category or 'no active error'}; {repeated_errors} repeated matching error(s).")
