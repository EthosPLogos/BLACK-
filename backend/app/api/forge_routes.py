"""
Black Forge API — website and project scaffolding.
  POST /api/forge/scaffold     — generate + write a complete project from a description
  GET  /api/forge/projects     — list all scaffolded projects
  GET  /api/forge/projects/{n}/tree  — file tree for a project
  POST /api/forge/projects/{n}/open  — open project folder in Finder
  GET  /api/forge/projects/{n}/file  — read a specific file
"""
import json
import re
import subprocess

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.web_builder_agent import WEB_BUILDER_SYSTEM
from app.services.file_writer import (
    PROJECTS_BASE_DIR,
    get_project_tree,
    list_projects,
    read_project_file,
    slugify,
    write_project_files,
)
from app.services.inference import call_inference

router = APIRouter(prefix="/api/forge", tags=["Black Forge"])


class ScaffoldRequest(BaseModel):
    description: str = Field(..., min_length=5, max_length=4000)
    project_name: str = Field(default="", max_length=60)
    framework: str = Field(default="auto")  # auto | html | react | nextjs | fastapi


class ScaffoldResponse(BaseModel):
    status: str
    project_name: str
    project_dir: str
    files_written: list[str]
    errors: list[dict]
    stack: str
    deploy: str
    setup_commands: list[str]
    preview_command: str
    agent_summary: str


def _extract_json_block(text: str) -> dict | None:
    """Extract the ```json ... ``` block from LLM output. Returns parsed dict or None."""
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try parsing the entire response as JSON (rare but possible)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    return None


def _build_scaffold_prompt(description: str, framework: str, project_name: str) -> str:
    stack_hint = ""
    if framework != "auto":
        stack_hint = f"\nTarget stack: {framework}."

    name_hint = ""
    if project_name:
        name_hint = f'\nProject name: "{project_name}" (use this slug exactly).'

    return (
        f"Build a complete, deployable website for this description:\n\n"
        f"{description}"
        f"{stack_hint}"
        f"{name_hint}\n\n"
        "Follow the full Architect → Build workflow. "
        "Write every file completely — no truncation, no placeholders. "
        "End your response with the required ```json file block."
    )


@router.post("/scaffold", response_model=ScaffoldResponse)
def scaffold(req: ScaffoldRequest):
    """
    Generate a complete website from a description and write it to disk.
    Uses frontier LLM (Claude Sonnet) for maximum code quality.
    """
    project_name = slugify(req.project_name) if req.project_name else ""

    prompt = _build_scaffold_prompt(req.description, req.framework, project_name)

    try:
        reply, provider = call_inference(prompt=prompt, system=WEB_BUILDER_SYSTEM, tier="frontier")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Inference failed: {str(exc)[:300]}")

    data = _extract_json_block(reply)
    if not data:
        raise HTTPException(
            status_code=422,
            detail=(
                "Black Forge did not return a parseable file block. "
                "Try a more specific description or specify a framework."
            ),
        )

    files = data.get("files") or []
    if not files:
        raise HTTPException(status_code=422, detail="Black Forge returned no files to write.")

    # Use LLM-chosen project name if user didn't specify one
    if not project_name:
        project_name = slugify(data.get("project_name") or req.description[:40])

    result = write_project_files(project_name, files)

    # Strip the json block from the agent summary shown to the user
    summary = re.sub(r"```json.*?```", "", reply, flags=re.DOTALL).strip()

    return ScaffoldResponse(
        status="built" if not result["errors"] else "built_with_errors",
        project_name=project_name,
        project_dir=result["project_dir"],
        files_written=result["written"],
        errors=result["errors"],
        stack=data.get("stack", "unknown"),
        deploy=data.get("deploy", ""),
        setup_commands=data.get("setup_commands") or [],
        preview_command=data.get("preview_command", ""),
        agent_summary=summary[:2000],
    )


@router.get("/projects")
def projects():
    return {"projects": list_projects(), "base_dir": str(PROJECTS_BASE_DIR)}


@router.get("/projects/{project_name}/tree")
def project_tree(project_name: str):
    result = get_project_tree(project_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/projects/{project_name}/file")
def project_file(project_name: str, path: str):
    try:
        content = read_project_file(project_name, path)
        return {"path": path, "content": content}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/projects/{project_name}/open")
def open_project(project_name: str):
    """Open the project folder in macOS Finder."""
    tree = get_project_tree(project_name)
    if "error" in tree:
        raise HTTPException(status_code=404, detail=tree["error"])
    subprocess.run(["open", tree["path"]], check=False)
    return {"opened": tree["path"]}
