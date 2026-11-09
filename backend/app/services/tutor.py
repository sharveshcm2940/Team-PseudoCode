from app.intelligence.tutor import generate_tutor_response

async def tutor_response(context:dict)->tuple[str,bool]:
    result=await generate_tutor_response(context)
    return result.response,result.fallback
