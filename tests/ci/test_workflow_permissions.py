"""ci.yml and release.yml run with least-privilege GITHUB_TOKEN permissions.

Each workflow sets a top-level ``permissions: contents: read`` (CodeQL's
actions/missing-workflow-permissions); the only write grants any job may ask
for are release.yml's ``publish: id-token: write`` (PyPI Trusted Publishing)
and ``attach-to-release: contents: write`` (uploading dist files to the GitHub
Release). The negative cases run the same checks on altered copies, so a
check that stops catching its case fails here.
"""

import copy
from pathlib import Path

import pytest
import yaml

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
CHECKED = ("ci.yml", "release.yml")

# (workflow, job) -> the write scopes that job may hold; any other write fails
ALLOWED_WRITES = {
    ("release.yml", "publish"): {"id-token"},
    ("release.yml", "attach-to-release"): {"contents"},
}
# (workflow, job, scope) that must be granted write
REQUIRED_WRITES = {("release.yml", "publish", "id-token")}


def load(name):
    return yaml.safe_load((WORKFLOWS / name).read_text())


def write_scopes(permissions):
    """The scopes a ``permissions`` value grants write on (``*`` for write-all)."""
    if permissions is None:
        return set()
    if isinstance(permissions, str):
        return {"*"} if permissions == "write-all" else set()
    return {scope for scope, level in permissions.items() if level == "write"}


def problems(name, workflow):
    """Every way ``workflow`` (parsed from ``name``) breaks least privilege."""
    found = []
    if workflow.get("permissions") != {"contents": "read"}:
        found.append(
            f"{name}: top-level permissions must be {{contents: read}}, "
            f"got {workflow.get('permissions')!r}"
        )
    jobs = workflow.get("jobs") or {}
    for job_id, job in jobs.items():
        writes = write_scopes(job.get("permissions"))
        extra = writes - ALLOWED_WRITES.get((name, job_id), set())
        if extra:
            found.append(f"{name}: job {job_id} asks for write on {sorted(extra)}")
    for wf, job_id, scope in REQUIRED_WRITES:
        if wf != name:
            continue
        job = jobs.get(job_id)
        if job is None:
            found.append(f"{name}: job {job_id} is missing")
        elif scope not in write_scopes(job.get("permissions")):
            found.append(f"{name}: job {job_id} must keep {scope}: write")
    return found


@pytest.mark.parametrize("name", CHECKED)
def test_workflow_is_least_privilege(name):
    assert problems(name, load(name)) == []


def test_release_keeps_its_two_write_grants():
    jobs = load("release.yml")["jobs"]
    assert jobs["publish"]["permissions"] == {"id-token": "write"}
    assert jobs["attach-to-release"]["permissions"] == {"contents": "write"}


@pytest.mark.parametrize("name", CHECKED)
def test_missing_top_level_block_fails(name):
    workflow = copy.deepcopy(load(name))
    del workflow["permissions"]
    assert any("top-level" in p for p in problems(name, workflow))


@pytest.mark.parametrize("name", CHECKED)
def test_broader_top_level_block_fails(name):
    workflow = copy.deepcopy(load(name))
    workflow["permissions"] = {"contents": "write"}
    assert any("top-level" in p for p in problems(name, workflow))


def test_publish_without_id_token_fails():
    workflow = copy.deepcopy(load("release.yml"))
    del workflow["jobs"]["publish"]["permissions"]
    assert any("id-token: write" in p for p in problems("release.yml", workflow))


@pytest.mark.parametrize(
    ("name", "job_id", "permissions"),
    [
        ("ci.yml", "test", {"contents": "write"}),
        ("ci.yml", "lint", {"pull-requests": "write"}),
        ("ci.yml", "coverage", "write-all"),
        ("release.yml", "build", {"id-token": "write"}),
        ("release.yml", "publish", {"id-token": "write", "contents": "write"}),
        ("release.yml", "attach-to-release", {"contents": "write", "packages": "write"}),
    ],
)
def test_other_write_grant_fails(name, job_id, permissions):
    workflow = copy.deepcopy(load(name))
    workflow["jobs"][job_id]["permissions"] = permissions
    assert any(f"job {job_id} asks for write" in p for p in problems(name, workflow))
