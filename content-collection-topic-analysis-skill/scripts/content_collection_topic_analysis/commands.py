from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from typing import Any


class SkillError(RuntimeError):
    """Base error for this skill."""


class CommandExecutionError(SkillError):
    """Raised when an external command fails."""


class IntegrationConfigError(SkillError):
    """Raised when required configuration is missing."""


@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str
    returncode: int


def run_command(command: list[str]) -> CommandResult:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    result = CommandResult(
        stdout=completed.stdout,
        stderr=completed.stderr,
        returncode=completed.returncode,
    )
    if completed.returncode != 0:
        raise CommandExecutionError(
            f"command failed: {' '.join(command)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def extract_first_json(text: str) -> Any:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char not in "[{":
            continue
        try:
            payload, _ = decoder.raw_decode(text[index:])
            return payload
        except json.JSONDecodeError:
            continue
    raise ValueError("no JSON payload found in command output")


def load_json_output(stdout: str, stderr: str = "") -> Any:
    sources = [stdout, stderr, "\n".join([stdout, stderr])]
    for source in sources:
        if not source.strip():
            continue
        try:
            return extract_first_json(source)
        except ValueError:
            continue
    raise ValueError("unable to parse JSON output")


def find_first_mapping_list(payload: Any, preferred_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    if isinstance(payload, dict):
        for key in preferred_keys:
            value = payload.get(key)
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                return value
            if isinstance(value, dict):
                result = find_first_mapping_list(value, preferred_keys)
                if result:
                    return result
        for value in payload.values():
            result = find_first_mapping_list(value, preferred_keys)
            if result:
                return result
    if isinstance(payload, list):
        for item in payload:
            result = find_first_mapping_list(item, preferred_keys)
            if result:
                return result
    return []


def find_first_scalar(payload: Any, keys: tuple[str, ...]) -> str | None:
    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        for value in payload.values():
            result = find_first_scalar(value, keys)
            if result:
                return result
    if isinstance(payload, list):
        for item in payload:
            result = find_first_scalar(item, keys)
            if result:
                return result
    return None

