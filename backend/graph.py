from typing import Literal, Optional
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from pydantic import BaseModel,Field

load_dotenv()

model = ChatOpenAI(model = "gpt-4o")

class My_state(MessagesState):
    human_prompt:str
    human_feedback:Optional[str]
    status:Literal["approved","feedback"]
    decision:Literal["YES","NO"]

class Route(BaseModel):
    step: Literal["YES","NO"] = Field(
        None,description= "The next step in the routing process") # type: ignore
    
router = model.with_structured_output(Route)

def inputs_agent(state: My_state):
    messages = state.get("messages", [])
    human_input = state["human_prompt"]
    if state.get("status") == "feedback":
        return {"messages": messages + [HumanMessage(content=f"(User correction) {human_input}")]}  # [web:79][web:3]
    return {"messages": messages + [HumanMessage(content=human_input)]}  

def eval_agent(state:My_state):
    print("Entered Eval Agent")
    """Route the input to the appropriate node"""
    # Run the augmented LLM with structured output to serve as routing logic
    user_inputs = " ".join(
        m.content for m in state["messages"] if isinstance(m, HumanMessage) # type: ignore
    ) # type: ignore
    decision = router.invoke(
        [
            SystemMessage(
                content=(
                    "Route the input text by checking if it includes all of these: "
                    "Source, Destination, Budget, and Number of days for the trip. "
                    "If all are present, return 'YES'; otherwise return 'NO'."
                    """
                    You are checking trip inputs. If the user gives corrections (like "change destination to Goa"),
                    update the trip details accordingly and mark decision as YES if complete."""
                )
            ),
            # Pass message *content* (string), not the object
            HumanMessage(content=user_inputs),
        ]
    )
    return {"decision": decision.step} # type: ignore

def route_decision(state:My_state):
    print("Route Decision entered")
    if state["decision"] == "YES":
        return "dummy_node_2"
    elif state["decision"] == "NO":
        return "dummy_node_1" 

def dummy_node_1(state:My_state):
    print("entered dummy 1")
    system_message = SystemMessage(content="Based on the missing details ask the user to enter the details . Check for only Source,Destination,Budget and number of days of the trip. Even if one of them is missing ask the question based on that in a short and sweet manner, Dont ask any recomendations anol. Just ask about the missing details")
    messages = state["messages"]
    response = model.invoke([system_message] + messages)
    return {"messages":[response]}

def dummy_node_2(state:My_state):
    print("entered dummy 2")
    system_message = SystemMessage(content = "Display all the aquired details like a table and wait for the human to approve. You are not supposed to make any plan Strictly. You are only to confirm the details   ")
    messages = state["messages"]
    response = model.invoke([system_message] + messages)
    return {"messages":[response]}

def travel_planner_agent(state: My_state):
    print("Entered Travel planner")
    # Use only human inputs to avoid re-triggering approval prompts from prior assistant text.
    human_only = [m for m in state.get("messages", []) if isinstance(m, HumanMessage)] 
    sys_msg = SystemMessage(content=(
        "Inputs are complete and approved. Generate the final itinerary now with:\n"
        "- Day-by-day schedule, activities, and timings\n"
        "- Lodging recommendations with approx. nightly rates\n"
        "- Local transport plan and costs\n"
        "- Meals and must-try spots\n"
        "- Budget breakdown with totals\n"
        "-Strictly Maintain the budget dont raise it over\n"
        "Do not ask for approval again."
    ))
    response = model.invoke([sys_msg] + human_only)
    return {"messages": [response]} 

def feedback_agent(state: My_state):
    # On approval, add nothing so the next hop is the planner with a clean context.
    if state.get("status") == "approved":
        return {} 
    msgs = state.get("messages", [])
    fb = state.get("human_feedback") or state.get("human_prompt") or ""  
    return {"messages": msgs + [HumanMessage(content=f"(User correction) {fb}")]}

def feedback_router(state: My_state) -> str:
    # Approved -> plan now; Feedback -> collect/update details. 
    return "travel_planner_agent" if state.get("status") == "approved" else "inputs_agent" 



memory = MemorySaver()
builder = StateGraph(My_state)

builder.add_node("inputs_agent",inputs_agent)
builder.add_node("eval_agent",eval_agent)
builder.add_node("dummy_node_1",dummy_node_1)
builder.add_node("dummy_node_2",dummy_node_2)
builder.add_node("feedback_agent",feedback_agent)
builder.add_node("travel_planner_agent",travel_planner_agent)

builder.add_edge(START,"inputs_agent")
builder.add_edge("inputs_agent","eval_agent")
builder.add_conditional_edges(
    "eval_agent",
    route_decision,
    {"dummy_node_1":"dummy_node_1","dummy_node_2":"dummy_node_2"}
)
builder.add_edge("dummy_node_1","inputs_agent")
builder.add_edge("dummy_node_2","feedback_agent")
builder.add_conditional_edges(
    "feedback_agent",
    feedback_router,
    {"travel_planner_agent": "travel_planner_agent", "inputs_agent": "inputs_agent"},
)
builder.add_edge("travel_planner_agent",END)


memory = MemorySaver()
graph = builder.compile(interrupt_after=["dummy_node_1","dummy_node_2"],checkpointer=memory)

__all__ = ["graph", "My_state"]