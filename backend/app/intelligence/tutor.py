from dataclasses import dataclass
import httpx
from app.config import settings

SYSTEM="""You are PALS, a careful DSA tutor. Use the verified learning context and requested response type. Follow the scaffold level. Never claim code is correct, change mastery, reveal hidden tests, shame the learner, or provide a complete solution below scaffold level 5. Give one useful next step and encourage reasoning."""

@dataclass(frozen=True)
class TutorResult:
    response:str
    provider:str
    model:str
    fallback:bool
    response_type:str

async def generate_tutor_response(context:dict,response_type:str="hint")->TutorResult:
    prompt=SYSTEM+f"\nResponse type: {response_type}\n\nVerified learning context:\n"+"\n".join(f"{key}: {value}" for key,value in context.items())
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response=await client.post(f"{settings.ollama_base_url}/api/generate",json={"model":settings.ollama_model,"prompt":prompt,"stream":False})
            response.raise_for_status();answer=response.json().get("response","").strip()
            if answer:return TutorResult(answer,"ollama",settings.ollama_model,False,response_type)
    except (httpx.HTTPError,KeyError,ValueError): pass
    level=int(context.get("scaffold_level",1));concept=context.get("concept","this concept");diagnosis=context.get("diagnosis","the last attempt")
    fallbacks={
        0:f"Try a harder {concept} problem independently. State the invariant before coding.",
        1:f"What must remain true after every step of {concept}? Test that statement on the smallest visible example.",
        2:f"Focus on {diagnosis}. Which single line changes the state involved in that diagnosis?",
        3:f"Trace one small input by hand. Record the active value and data-structure state after each operation.",
        4:f"Separate {concept} into initialization, repeated update, boundary handling, and termination. Verify each part in that order.",
        5:f"Worked path: state the invariant, initialize it for the smallest input, apply one update, check the boundary, and verify termination before translating each stage to Java.",
    }
    return TutorResult(fallbacks.get(level,fallbacks[1]),"deterministic","pals-fallback-v2",True,response_type)
