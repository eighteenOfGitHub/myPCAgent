# shared/greeting_schemas.py

from pydantic import BaseModel

class GreetingResponse(BaseModel):
    message: str
