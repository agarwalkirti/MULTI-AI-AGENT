# data flow: UI → FastAPI → convert_to_langchain_messages() → List[BaseMessage] → SystemMessage injected → LangGraph agent → Groq → Response
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch

from langgraph.prebuilt import create_react_agent
from langchain_core.messages.ai import AIMessage
from langchain_core.messages import SystemMessage

from app.config.settings import settings

def get_response_from_ai_agents(llm_id , query , allow_search ,system_prompt):

    # llm initialized
    llm = ChatGroq(model=llm_id)

    # tavily Tool Injection
    tools = [TavilySearch(max_results=2)] if allow_search else []

    #create_react_agent implements ReAct Pattern: Reason + Act (tool call), Observe, Repeat
    agent = create_react_agent(
        model=llm,
        tools=tools,
        #state_modifier=system_prompt # controls AI behavior and response style
    )

    # Inject system prompt correctly
    if system_prompt:
        query = [SystemMessage(content=system_prompt)] + query

    #create_react_agent expects the state to follow a structured schema,{ "messages": [BaseMessage, BaseMessage, ...]}
    # Where each message must be an object like: HumanMessage ,AIMessage, SystemMessage,ToolMessage
    # LangGraph expects structured state
    state = {
        "messages": query   # query is already List[BaseMessage]
    }

    # Invoke agent
    response = agent.invoke(state)

    messages = response.get("messages",[])

    # Extract only AI responses
    ai_messages = [message.content for message in messages if isinstance(message,AIMessage)] #filtered only AI messages from the response and extracted their content

    return ai_messages[-1] if ai_messages else "No response generated." # fetch latest messsage -1 means the last message in the list



    
    







