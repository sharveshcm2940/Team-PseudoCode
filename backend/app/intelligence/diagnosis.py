import re
from dataclasses import asdict,dataclass
from app.models import Attempt,Problem

@dataclass(frozen=True)
class Diagnostic:
    category:str
    severity:str
    title:str
    explanation:str
    evidence:str
    suggested_action:str
    confidence:float
    misconception:bool=False

CATEGORY_ALIASES={
    "Compilation error":"compilation_error","Logical error":"logical_error","Incorrect condition":"logical_error",
    "Boundary condition error":"boundary_condition","Time complexity issue":"time_complexity",
    "Conceptual misunderstanding":"conceptual_misconception",
}

def canonical_category(value:str)->str:
    return CATEGORY_ALIASES.get(value,value.strip().lower().replace(" ","_"))

def _item(category,severity,title,explanation,evidence,action,confidence,misconception=False):
    return Diagnostic(category,severity,title,explanation,(evidence or "No sensitive test details exposed.")[:2000],action,confidence,misconception)

def diagnose_all(attempt:Attempt,problem:Problem)->list[dict]:
    output=attempt.compiler_output or ""
    text=output.lower()
    failures=[result for result in attempt.results if not result.get("passed")]
    visible_inputs=[str(result.get("input")) for result in failures if result.get("input") is not None]
    results:list[Diagnostic]=[]
    rules=[
        (r"emptystackexception|stack underflow|pop from empty",("stack_underflow","high","Stack underflow","A pop or peek was attempted when the stack was empty.","Guard the operation with an empty-stack check.",.97,True)),
        (r"stackoverflowerror|stack overflow",("stack_overflow","high","Stack overflow","The call stack or bounded stack exceeded its safe capacity.","Check recursion progress and stack capacity before adding another item.",.96,True)),
        (r"nullpointerexception",("null_pointer_error","high","Null reference","Code used an object reference before it pointed to a valid object.","Trace where the reference is initialized and add the appropriate base case.",.96,False)),
        (r"arrayindexoutofboundsexception|indexoutofboundsexception",("array_index_error","high","Array index outside bounds","An index was smaller than zero or at least the collection length.","Check loop bounds and every index derived from input.",.96,False)),
        (r"time limit|time limit exceeded",("time_complexity","high","Time complexity issue","Execution exceeded the configured time limit.","Reconsider the algorithmic complexity and repeated work.",.92,False)),
    ]
    for pattern,data in rules:
        if re.search(pattern,text,re.I): results.append(_item(*data[:4],output,*data[4:]))
    compile_markers=("cannot find symbol","';' expected","incompatible types","class, interface", "illegal start")
    if output and (any(marker in text for marker in compile_markers) or "compile" in text):
        results.append(_item("compilation_error","high","Java compilation error","The compiler rejected the program before it could run.",output,"Inspect the reported line and fix syntax, symbols, or types first.",.99))
    problem_text=f"{problem.title} {problem.statement}".lower()
    if "stack" in problem_text and any(token in text for token in ("lifo","fifo")):
        results.append(_item("lifo_misconception","high","LIFO order misconception","The observed order suggests stack and queue behavior were confused.",output,"Use the Stack visualizer and identify which end is the top.",.90,True))
    if any(token in problem_text for token in ("parentheses","bracket")) and failures:
        results.append(_item("parentheses_validation","medium","Delimiter matching misconception","The validator failed a case involving nested or unmatched delimiters.","A visible validation case failed.","Trace pushes for opening symbols and pops for matching closing symbols.",.82,True))
    if failures and any(value.strip() in {"[]","0","1",""} for value in visible_inputs):
        results.append(_item("boundary_condition","medium","Boundary condition error","The smallest or empty visible input did not produce the expected behavior.","A visible boundary case failed.","Check initialization, empty inputs, and loop endpoints.",.84))
    if failures and not results:
        results.append(_item("logical_error","medium","Possible logical error",f"{len(failures)} evaluated case(s) produced an incorrect result.","Output differed from the expected result; hidden inputs remain private.","Trace conditions and state changes with the visible example.",.68))
    if not results:
        results.append(_item("unknown_error","low","No known pattern identified","The available evidence does not match a supported diagnostic rule.",output,"Compare the visible expected and actual behavior, then trace the invariant.",.25))
    return [asdict(result) for result in sorted(results,key=lambda result:result.confidence,reverse=True)]

def primary_diagnosis(attempt:Attempt,problem:Problem)->dict:
    details=diagnose_all(attempt,problem); primary=details[0]
    return {"category":primary["category"],"evidence":primary["evidence"],"confidence":primary["confidence"],"recommended_response":primary["suggested_action"],"severity":primary["severity"],"title":primary["title"],"explanation":primary["explanation"],"suggested_action":primary["suggested_action"],"misconception":primary["misconception"],"details":details}
