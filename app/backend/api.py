from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from pydantic import Field
from typing import List
import uuid 
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.ai_agent import get_response_from_ai_agents
from app.config.settings import settings
from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)

#FastAPI uses Pydantic to: Validate request body ,Auto-generate Swagger docs,Enforce type safety
#Flow: Client → FastAPI → Agent Layer → LLM (+ tools) → Response
#FastAPI service: Accepts request,Validates model name,Passes input to agent layer ,Returns AI response
app = FastAPI(title="MULTI AI AGENT") # initialize FastAPI app with a title

# Request Schema
## Each message must contain: role → user / assistant / system ,content → actual text
class ChatMessage(BaseModel):
    role: str= Field(..., description="user | assistant | system")
    content: str

class RequestState(BaseModel):
    model_name: str
    system_prompt: str
    messages: List[ChatMessage]
    allow_search: bool

# Helper: Convert API Messages to LangChain BaseMessage format 
# Convert API schema → LangChain schema. Because our agent expects: List[BaseMessage] NOT raw dicts.
def convert_to_langchain_messages(messages: List[ChatMessage]):
    """
    Convert API message schema into LangChain BaseMessage objects.
    """
    converted_messages = []
    
    for msg in messages:
        role = msg.role.lower()
        #  API Role - LangChain Class , user - HumanMessage ,assistant	- AIMessage, system - SystemMessage
        if role == "user":
            converted_messages.append(HumanMessage(content=msg.content))

        elif role == "assistant":
            converted_messages.append(AIMessage(content=msg.content))

        elif role == "system":
            converted_messages.append(SystemMessage(content=msg.content))

        else:
            raise ValueError(f"Invalid role: {msg.role}")

    return converted_messages

# Chat Endpoint
@app.post("/chat")
async def chat_endpoint(request: RequestState):
    #uuid: Unique identifier per request, Helps debugging logs, Helps distributed tracing
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Received request for model: {request.model_name}")

    # Validate model
    if request.model_name not in settings.ALLOWED_MODEL_NAMES:
        logger.warning(f"[{request_id}] Invalid model name")
        raise HTTPException(status_code=400, detail="Invalid model name")

    try:
        # Convert incoming messages to LangChain format
        lc_messages = convert_to_langchain_messages(request.messages)

        # Call agent layer
        response = get_response_from_ai_agents(
            llm_id=request.model_name,
            query=lc_messages,
            allow_search=request.allow_search,
            system_prompt=request.system_prompt
        )

        logger.info(f"[{request_id}] Successfully generated AI response {request.model_name}")

        return {
            "request_id": request_id,
            "model": request.model_name,
            "response": response
        }

    except ValueError as ve:
        logger.error(f"[{request_id}] Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.error(f"[{request_id}] Error during response generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(
                CustomException(
                    message="Failed to get AI response",
                    error_detail=e
                )
            )
        )
    
#health end point for startup checks and monitoring
@app.get("/health")
async def health_check():
    return {"status": "ok"}
print("ROUTES REGISTERED:", [route.path for route in app.routes])

    



