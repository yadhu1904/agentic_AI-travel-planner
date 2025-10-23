from fastapi import APIRouter
from uuid import uuid4
from backend.models import StartRequest, GraphResponse, ResumeRequest
from backend.graph import graph

note = APIRouter()



from langchain_core.messages import AIMessage

def get_last_assistant_response(messages):
    # Prefer the latest AIMessage (assistant output). [web:79]
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) or getattr(msg, "type", "") == "ai":
            return msg.content  # [web:79][web:77]
    # Fallback to any content-bearing message. [web:79]
    for msg in reversed(messages):
        if hasattr(msg, "content"):
            return msg.content  # [web:79]
    return ""  # [web:79]

def run_graph_and_response(input_state, config):
    result = graph.invoke(input_state, config)     # run or resume [web:88]
    state = graph.get_state(config)                # snapshot after this step [web:88]
    next_nodes = state.next or []                  # tuple of upcoming node names [web:112]

    messages = result.get("messages", [])
    assistant_response = get_last_assistant_response(messages)
    if next_nodes:
        run_status = "awaiting_feedback" if "feedback_agent" in next_nodes else "in_progress"  # [web:88]
    else:
        run_status = "finished" 
    return GraphResponse(
        thread_id=config["configurable"]["thread_id"],
        run_status=run_status,
        assistant_response=assistant_response,
    )



@note.post("/graph/start", response_model=GraphResponse)
def start_graph(request: StartRequest):
    """
    First user message starts a new thread.
    """
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    # initial state
    initial_state = {
        "human_prompt": request.human_prompt,
        "messages": []  # ensure a message history list exists
    }
    return run_graph_and_response(initial_state, config)


# backend/app/api.py

@note.post("/graph/resume", response_model=GraphResponse)
def resume_graph(request: ResumeRequest):
    config = {"configurable": {"thread_id": request.thread_id}}

    # Inspect where the graph is right now
    state = graph.get_state(config)
    next_nodes = state.next or []  # empty means END [web:10]

    if next_nodes:
        # Normal interrupt resume
        update_state = {"status": request.review_action}  # "approved" or "feedback" [web:88]
        if request.review_action == "feedback":
            correction = request.human_feedback or ""
            update_state["human_feedback"] = correction  # for feedback_agent [web:88]
            update_state["human_prompt"] = correction    # for inputs_agent [web:88]
        else:
            update_state["human_prompt"] = ""            # no new user text on approve [web:88]
        graph.update_state(config, update_state)         # persist into checkpoint [web:88]
        return run_graph_and_response(None, config)      # continue from interrupt [web:88]

    # Finished flow: start a new turn in the SAME thread with the new user text
    initial_state = {
        "human_prompt": request.human_feedback or "",    # next user message [web:88]
        "status": "feedback",                            # treat as iterative follow-up [web:88]
        "messages": []                                   # reducer will merge with history [web:88]
    }
    return run_graph_and_response(initial_state, config)  # start next turn with memory [web:88]
