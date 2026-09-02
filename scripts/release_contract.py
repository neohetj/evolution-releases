#!/usr/bin/env python3
"""Validate component releases and compose immutable Runner bundles."""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urlparse


SUPPORTED_PLATFORMS = {
    "darwin-arm64": ("darwin", "arm64"),
    "darwin-amd64": ("darwin", "amd64"),
    "windows-amd64": ("windows", "amd64"),
}
COMPONENT_REPOSITORIES = {
    "operator": "neohetj/operator",
    "keymaker-runner-step": "neohetj/keymaker",
}
SAFE_VERSION = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._-]*$")
SAFE_COMPONENT = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SOURCE_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SOURCE_COMMIT = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ContractError(ValueError):
    """A release manifest violates the public distribution contract."""


def _require_keys(value: Dict[str, Any], expected: Iterable[str], label: str) -> None:
    expected_set = set(expected)
    actual = set(value)
    if actual != expected_set:
        raise ContractError(
            f"{label} keys must be {sorted(expected_set)}, got {sorted(actual)}"
        )


def _require_version(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SAFE_VERSION.fullmatch(value):
        raise ContractError(f"{label} is invalid")
    return value


def _validate_source(value: Any) -> None:
    if not isinstance(value, dict):
        raise ContractError("source must be an object")
    _require_keys(value, ("repository", "commit"), "source")
    if not isinstance(value["repository"], str) or not SOURCE_REPOSITORY.fullmatch(
        value["repository"]
    ):
        raise ContractError("source repository is invalid")
    if not isinstance(value["commit"], str) or not SOURCE_COMMIT.fullmatch(
        value["commit"]
    ):
        raise ContractError("source commit must be a lowercase 40-character SHA")


def _validate_artifact(component: str, version: str, value: Any) -> str:
    if not isinstance(value, dict):
        raise ContractError("artifact must be an object")
    _require_keys(
        value,
        ("platform", "os", "arch", "filename", "url", "sha256"),
        "artifact",
    )
    platform = value["platform"]
    if platform not in SUPPORTED_PLATFORMS:
        raise ContractError(f"unsupported platform {platform!r}")
    expected_os, expected_arch = SUPPORTED_PLATFORMS[platform]
    if value["os"] != expected_os or value["arch"] != expected_arch:
        raise ContractError(f"artifact OS/architecture does not match {platform}")
    extension = ".exe" if expected_os == "windows" else ""
    expected_filename = (
        f"{component}_{version}_{expected_os}_{expected_arch}{extension}"
    )
    if value["filename"] != expected_filename:
        raise ContractError(
            f"artifact filename must be {expected_filename}, got {value['filename']!r}"
        )
    parsed = urlparse(value["url"] if isinstance(value["url"], str) else "")
    if parsed.scheme != "https" or not parsed.netloc:
        raise ContractError("artifact URL must use HTTPS")
    if Path(parsed.path).name != expected_filename:
        raise ContractError("artifact URL filename does not match the artifact filename")
    if not isinstance(value["sha256"], str) or not SHA256.fullmatch(value["sha256"]):
        raise ContractError("artifact SHA-256 must be 64 lowercase hexadecimal characters")
    return platform


def validate_component_manifest(
    value: Any, *, expected_component: Optional[str] = None
) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("component manifest must be an object")
    _require_keys(
        value,
        ("schema_version", "component", "version", "source", "artifacts"),
        "component manifest",
    )
    if value["schema_version"] != "2":
        raise ContractError("component manifest schema_version must be 2")
    component = value["component"]
    if not isinstance(component, str) or not SAFE_COMPONENT.fullmatch(component):
        raise ContractError("component identity is invalid")
    if expected_component is not None and component != expected_component:
        raise ContractError(
            f"component must be {expected_component}, got {component}"
        )
    version = _require_version(value["version"], "component version")
    _validate_source(value["source"])
    expected_repository = COMPONENT_REPOSITORIES.get(component)
    if expected_repository is None or value["source"]["repository"] != expected_repository:
        raise ContractError(
            f"component {component} source repository must be {expected_repository}"
        )
    if not isinstance(value["artifacts"], list):
        raise ContractError("artifacts must be an array")
    platforms = [
        _validate_artifact(component, version, artifact)
        for artifact in value["artifacts"]
    ]
    if len(set(platforms)) != len(platforms):
        raise ContractError("component manifest contains a duplicate platform")
    if set(platforms) != set(SUPPORTED_PLATFORMS):
        raise ContractError(
            "component platform set must be darwin-arm64, darwin-amd64, windows-amd64"
        )
    return value


def validate_runner_bundle(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("Runner bundle must be an object")
    _require_keys(
        value, ("schema_version", "bundle", "version", "components"), "Runner bundle"
    )
    if value["schema_version"] != "2" or value["bundle"] != "runner":
        raise ContractError("Runner bundle metadata is invalid")
    _require_version(value["version"], "Runner bundle version")
    components = value["components"]
    if not isinstance(components, dict):
        raise ContractError("Runner bundle components must be an object")
    _require_keys(
        components, ("operator", "keymaker-runner-step"), "Runner bundle components"
    )
    operator = validate_component_manifest(
        components["operator"], expected_component="operator"
    )
    runner_step = validate_component_manifest(
        components["keymaker-runner-step"],
        expected_component="keymaker-runner-step",
    )
    operator_platforms = {item["platform"] for item in operator["artifacts"]}
    runner_step_platforms = {item["platform"] for item in runner_step["artifacts"]}
    if operator_platforms != runner_step_platforms:
        raise ContractError("Runner bundle component platform sets do not match")
    return value


def compose_runner_bundle(
    version: str, operator: Any, runner_step: Any
) -> Dict[str, Any]:
    _require_version(version, "Runner bundle version")
    validate_component_manifest(operator, expected_component="operator")
    validate_component_manifest(
        runner_step, expected_component="keymaker-runner-step"
    )
    bundle = {
        "schema_version": "2",
        "bundle": "runner",
        "version": version,
        "components": {
            "operator": copy.deepcopy(operator),
            "keymaker-runner-step": copy.deepcopy(runner_step),
        },
    }
    return validate_runner_bundle(bundle)


def _load(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: str, value: Any) -> None:
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    component = subparsers.add_parser("validate-component")
    component.add_argument("manifest")
    component.add_argument("--component", required=True)
    bundle = subparsers.add_parser("validate-bundle")
    bundle.add_argument("manifest")
    compose = subparsers.add_parser("compose-runner-bundle")
    compose.add_argument("--version", required=True)
    compose.add_argument("--operator", required=True)
    compose.add_argument("--runner-step", required=True)
    compose.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "validate-component":
        validate_component_manifest(_load(args.manifest), expected_component=args.component)
    elif args.command == "validate-bundle":
        validate_runner_bundle(_load(args.manifest))
    else:
        _write(
            args.output,
            compose_runner_bundle(
                args.version, _load(args.operator), _load(args.runner_step)
            ),
        )


if __name__ == "__main__":
    main()
