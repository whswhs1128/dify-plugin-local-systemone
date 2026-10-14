import json
from collections.abc import Generator
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


def _read_questions(value: Any) -> dict[str, Any]:
    """Parse the JSON-encoded System One `questions` field from a Dify tool node."""
    if isinstance(value, str):
        if not value.strip():
            raise ValueError("questions must not be empty; supply a JSON object")
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"questions must be valid JSON (not Python dict syntax): {exc.msg}"
            ) from exc
    if not isinstance(value, dict) or not value:
        raise ValueError("questions must be a non-empty JSON object")
    for name, definition in value.items():
        if not isinstance(name, str) or not isinstance(definition, dict):
            raise ValueError("questions must map question names to object definitions")
        if not isinstance(definition.get("type"), str):
            raise ValueError(f"questions.{name}.type must be provided")
    return value


def _prepare_payload(parameters: dict[str, Any]) -> dict[str, Any]:
    model = str(parameters.get("model") or "").strip()
    state = str(parameters.get("state") or "").strip()
    if not model:
        raise ValueError("model must not be empty; use the ID returned by /v1/models")
    if not state:
        raise ValueError("state must not be empty; bind state to START/sys.query")
    if len(model) > 1024 or len(state) > 100000:
        raise ValueError("model/state input exceeds allowed length")

    questions = _read_questions(parameters.get("questions"))
    return {"model": model, "state": state, "questions": questions}


def _parse_result(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("answers"), dict):
        raise RuntimeError("System One response has no answers object")
    answers = data["answers"]
    route_answer = answers.get("route")
    if not isinstance(route_answer, dict):
        route_answer = {}
    route = route_answer.get("choice")
    if not isinstance(route, str):
        route = ""
    raw = route_answer.get("probabilities")
    probabilities = raw if isinstance(raw, dict) else {}
    selected = probabilities.get(route, 0.0)
    try:
        probability = float(selected) if selected is not None else 0.0
    except (TypeError, ValueError):
        probability = 0.0
    diagnostics = data.get("diagnostics")
    return {
        "route": route,
        "probability": probability,
        "probabilities": probabilities,
        "answers": answers,
        "diagnostics": diagnostics if isinstance(diagnostics, dict) else {},
    }


class ClassifyIntentTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        payload = _prepare_payload(tool_parameters)
        credentials = self.runtime.credentials or {}
        base_url = str(credentials.get("base_url") or "").strip().rstrip("/")
        api_key = str(credentials.get("api_key") or "").strip()
        if not base_url:
            raise ValueError("Configure the vLLM Base URL in plugin provider settings")

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            response = requests.post(
                base_url + "/v1/systemone",
                json=payload,
                headers=headers,
                timeout=(5, 40),
                allow_redirects=False,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise RuntimeError(
                "System One request failed; verify vLLM connectivity, API authentication, model and questions"
            ) from exc
        except ValueError as exc:
            raise RuntimeError("System One server response is not valid JSON") from exc

        result = _parse_result(data)
        for name, value in result.items():
            yield self.create_variable_message(name, value)
        yield self.create_json_message(result)
        yield self.create_text_message(result["route"] or json.dumps(result["answers"], ensure_ascii=False))
