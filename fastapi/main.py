# main.py

import textwrap
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List

from clients.openai_client import OpenAIClient  # assumes class is implemented
import os

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

        Using the above code snippet, generate a README.md file such \
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