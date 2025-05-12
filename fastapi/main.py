# main.py

import textwrap
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List
from clients.s3_client import S3Client

from clients.openai_client import OpenAIClient  # assumes class is implemented
import os

import asyncio
from fastapi import APIRouter
from clients.openai_client import OpenAIClient  # assuming it supports async

# Load OpenAI client (assumes YAML path is hardcoded or env-provided)
openai_client = OpenAIClient("configs/openai_config.yaml")

# FastAPI app setup
app = FastAPI(title="CatGPT API")

# CORS for local dev
origins = ["http://localhost:8000", "http://localhost:80"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_s3 = S3Client('configs/s3_config.yaml')

# Pydantic model
class PromptRequest(BaseModel):
    prompt: str
    system: str = "You are a helpful assistant."  # Optional system prompt

# Endpoint: Markdown
@app.post("/markdown")
def get_markdown_response(request: PromptRequest) -> Dict[str, str]:
    try:
        response = openai_client.get_text(
            prompt=request.prompt,
            role="user",
            messages=[{"role": "system", "content": request.system}]
        )
        return {"type": "markdown", "content": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Endpoint: Markdown README.md
@app.post("/readme")
def get_readme_md_response(request: PromptRequest) -> Dict[str, str]:
    try:
        readme = f"""
        ## Context

        Using the above code snippet(s), generate a README.md file such \
        that an LLM reading this file can understand what this code \
        does, and how to use it. 
        
        ## Output Specifications

        You must ONLY return a markdown code block, i.e. ```md ```.
        """
        prompt = textwrap.dedent(f"## Prompt\n{request.prompt}\n{readme}")
        
        response = openai_client.get_text(
            prompt=prompt,
            role="user",
            messages=[{"role": "system", "content": request.system}])
        return {"type": "markdown", "content": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint: Python Code
@app.post("/python")
def get_python_response(request: PromptRequest) -> Dict[str, str]:
    try:
        prompt = request.prompt
        prompt = prompt + "As a reminder, you must ONLY return python code inside a ```py ``` code block."
        code = openai_client.get_python(
            prompt=prompt,
            role="user",
            messages=[{"role": "system", "content": request.system}]
        )
        return {"type": "python", "content": code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class BasicResponse(BaseModel):
    res: Dict
    
class BasicListResponse(BaseModel):
    res: List[BasicResponse]


OUTPUT_STRUCTS = {
    "BasicResponse": BasicResponse,
    "BasicListResponse": BasicListResponse
}

class JSONPromptRequest(BaseModel):
    prompt: str
    system: str = "You are a helpful assistant." 
    schema_name: str

# Endpoint: JSON Output
@app.post("/json")
def get_json_response(req: JSONPromptRequest):
    if req.schema_name not in OUTPUT_STRUCTS:
        raise HTTPException(status_code=400, detail="Invalid schema_name")
    print(req)
    schema_model = OUTPUT_STRUCTS[req.schema_name]
    print(schema_model)
    output_struct = {
        "type": "json_schema",
        "json_schema": {
            "name": schema_model.__name__,
            "schema": schema_model.model_json_schema()
        }
    }
    content = openai_client.get_json(
        prompt=req.prompt,
        output_struct=output_struct,
        role="user"
    )

    print(f"RESPONSE:\t{content}")

    return {"type": "json", "content": content}

@app.post("/multi_markdown")
async def get_multi_markdown_response(request: PromptRequest):
    personas = {
        "Clinical Data SME": "You are a functional clinical data expert. You started your career working in the clinical data management space, particularly developing functional mapping specifications for SDTM/ADaM standards.",
        "Pharma CTO": "You are a CTO for a large pharma company. You started your career working in the clinical data management space, particularly researching SDTM/ADaM automation.",
        "Statistician": "You are a statistician, specializing in clinical trials and technology, who values precision and uncertainty. You started your career working as a SAS/R programmer for SDTM/ADaM conversion, but disliked how old-school the process felt.",
        "Software Engineer": "You are a software engineer, specializing in clinical trials and technology. You think it's possible to use agentic frameworks and solid full-stack apps to automate the entire clinical data management pipeline, even the data diversity seen in the clinical world."
    }

    async def get_response(name, persona_prompt):
        openai_client_temp = OpenAIClient("configs/openai_config.yaml")
        response = openai_client_temp.get_text(
            prompt=request.prompt,
            role="user",
            messages=[{"role": "system", "content": persona_prompt}]
        )
        return {"persona": name, "content": response}

    tasks = [get_response(name, prompt) for name, prompt in personas.items()]
    responses = await asyncio.gather(*tasks)

    return {"type": "markdown_multi", "responses": responses}

class ChatRequest(BaseModel):
    chat_id: str
    prompt: str
    type: str
    schema_name: str = None  # Optional if not using JSON
    system: str = "You are a helpful assistant."  # ✅ Add this

@app.post("/chat")
def chat_handler(request: ChatRequest):
    chat_id = request.chat_id or "chat-0001"
    key = f"{_s3.prefixes['chats']}/{chat_id}.json"
    # Load prior messages (if any)
    try:
        messages = _s3.read_json(key)
    except Exception:
        messages = []

    # Add user prompt
    messages.append({"role": "user", "type": request.type, "content": request.prompt})

    # Build LLM message context
    context = [{"role": "system", "content": request.system}]
    context += [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] in ["user", "assistant"]]

    # Call OpenAI based on type
    if request.type == "markdown":
        output = openai_client.get_text(request.prompt, "user", messages=context)
    elif request.type == "python":
        prompt = request.prompt + "\nAs a reminder, you must ONLY return python code inside a ```py ``` code block."
        output = openai_client.get_python(prompt, "user", messages=context)
    elif request.type == "json":
        schema_model = OUTPUT_STRUCTS.get(request.schema_name)
        if not schema_model:
            raise HTTPException(status_code=400, detail="Invalid schema_name")
        output_struct = {
            "type": "json_schema",
            "json_schema": {
                "name": schema_model.__name__,
                "schema": schema_model.model_json_schema()
            }
        }
        output = openai_client.get_json(request.prompt, output_struct, "user")
    else:
        raise HTTPException(status_code=400, detail="Unsupported type")

    # Save assistant response
    messages.append({"role": "assistant", "type": request.type, "content": output})
    _s3.write_json(key, messages)

    return {"chat_id": chat_id, "response": output}


@app.get("/chat/history")
def get_chat_history(chat_id: str = Query(...)):
    key = f"{_s3.prefixes['chats']}/{chat_id}.json"
    try:
        messages = _s3.read_json(key)
        return {"chat_id": chat_id, "messages": messages}
    except Exception:
        return {"chat_id": chat_id, "messages": []}
    



