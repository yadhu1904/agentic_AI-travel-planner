# Smart Travel Planner

A chat-based travel planner with a Streamlit frontend and a FastAPI + LangGraph backend that collects trip details, asks for a single approval, generates a full itinerary, and keeps the conversation going for follow‑ups.[11][10]

## Features

- Conversational flow that validates Source, Destination, Number of days, and Budget, then pauses once for approval before creating the plan.[12][11]
- Human‑in‑the‑loop using LangGraph interrupts to wait for Approve or Feedback, with clean resume routing based on the user’s choice.[13][12]
- Streamlit chat UI with a thinking spinner, approval buttons shown only when the backend is awaiting approval, and the input disabled during approval to avoid duplicate prompts.[14][10]
- Checkpointed memory so the thread continues after the itinerary is produced, enabling follow‑up edits or questions without losing context.[15][11]

## Tech stack

- Backend: FastAPI + LangGraph (StateGraph, conditional edges, interrupts, persistence).[11][12]
- LLM: LangChain ChatOpenAI (e.g., gpt‑4o) configured via environment variables.[16]
- Frontend: Streamlit chat components (chat_input, chat_message, forms, spinner, rerun).[17][10]

## Project structure

- backend/app/graph.py: LangGraph nodes (inputs_agent, eval_agent, dummy_node_1, dummy_node_2, feedback_agent, travel_planner_agent), edges, and interrupt configuration.[12][11]
- backend/app/api.py: FastAPI routes /graph/start and /graph/resume, run status via state.next, and response selection.[18][11]
- frontend.py: Streamlit chat UI, approval buttons rendered only while awaiting approval, feedback form, and spinners during requests.[10][14]

## Prerequisites

- Python 3.10+ and a working virtual environment for isolated dependencies.[19]
- An OpenAI API key in a local .env file (OPENAI_API_KEY=...) or environment variable for ChatOpenAI.[16]

## Setup

1) Clone and create a virtual environment.[19]
2) Install backend and frontend requirements as per your requirements.txt files.[19]
3) Create a .env file in the project root and add the model credentials (e.g., OPENAI_API_KEY=your_key).[16]

Example .env:  
```
OPENAI_API_KEY=your_openai_api_key
```


Recommended .gitignore entries:  
```
# env files
.env
*.env
**/.env

# virtual environments
venv/
.venv/
```


## Running locally

- Start the backend API (FastAPI) with hot reload.[20]
```
python -m uvicorn backend.app.api:note  --reload  --env-file .env
```


- Start the Streamlit frontend.[10]
```
streamlit run frontend.py
```


- If your backend runs on a different host/port, update API_BASE in frontend.py accordingly.[10]

## How it works

- Input collection: The graph appends each user message and evaluates whether the four required fields are present.[11]
- Approval gate: If complete, an approval prompt is shown and the graph interrupts; the frontend displays Approve/Feedback buttons while the chat input is disabled.[12][10]
- Approve: The flow resumes directly to the planner node, which generates the final itinerary in one response.[11]
- Feedback: The correction is appended as a new message and the flow re‑checks completeness, returning to the approval gate only when ready.[13][11]

## Frontend UX

- chat_input is disabled during approval prompts to guide users to click Approve or Give Feedback.[10]
- chat_message is used for both user and assistant bubbles; a spinner shows a “thinking” state while requests are in flight.[14][17]
- The page reruns after each request to refresh UI based on the backend run_status (awaiting_feedback, in_progress, finished).[21]

## Environment tips

- Ensure load order: the .env must be read before initializing ChatOpenAI so the key is available at model construction time.[16]
- Alternatively, pass --env-file .env to your app server process if you prefer CLI‑driven env loading.[20]

## Troubleshooting

- Approval shown multiple times: Only render buttons when backend run_status is awaiting_feedback and disable chat_input during that state.[21][10]
- Plan produced before approval: Keep the approval node short and non‑generative, and let the planner node produce the itinerary after explicit approval.[12][11]
- .env not recognized: Verify the key name OPENAI_API_KEY and that the environment is loaded before model creation or use a server flag to load the env file.[20][16]

## License


[1](https://python.langchain.com/docs/tutorials/llm_chain/)
[2](https://langchain-ai.github.io/langgraph/concepts/template_applications/)
[3](https://www.langchain.com)
[4](https://sourceforge.net/projects/langchain.mirror/files/langchain-xai==1.0.0a1/README.md/download)
[5](https://www.youtube.com/watch?v=MV7Tdetoi8I)
[6](https://python.langchain.com/docs/tutorials/rag/)
[7](https://python.langchain.com/docs/tutorials/agents/)
[8](https://templates.langchain.com)
[9](https://www.youtube.com/watch?v=tcqEUSNCn8I)
[10](https://docs.streamlit.io/develop/api-reference/chat/st.chat_input)
[11](https://langchain-ai.github.io/langgraph/reference/graphs/)
[12](https://docs.langchain.com/oss/python/langgraph/interrupts)
[13](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/wait-user-input/)
[14](https://docs.streamlit.io/develop/api-reference/status/st.spinner)
[15](https://langchain-ai.github.io/langgraph/concepts/persistence/)
[16](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html)
[17](https://docs.streamlit.io/develop/api-reference/chat/st.chat_message)
[18](https://langchain-ai.github.io/langgraph/concepts/low_level/)
[19](https://docs.github.com/articles/ignoring-files)
[20](https://stackoverflow.com/questions/73727750/how-to-pass-env-file-to-fastapi-app-via-command-line)
[21](https://docs.streamlit.io/develop/api-reference/execution-flow/st.rerun)


