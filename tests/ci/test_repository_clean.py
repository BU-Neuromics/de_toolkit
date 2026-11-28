"""The session guard in tests/conftest.py (repository_left_clean) sees the
files a test run leaves in the repository (#210)."""

import shutil
import subprocess

import pytest

from conftest import files_left_behind, untracked_files

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / ".gitignore").write_text(".coverage\n")
    (repo / "tracked.txt").write_text("x\n")
    git(repo, "add", ".")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-qm", "init")
    return repo


def test_a_clean_tree_has_no_untracked_files(repo):
    assert untracked_files(repo) == set()


def test_a_directory_left_behind_is_listed_file_by_file(repo):
    # what tests/de/test_de.py::test_R_check_names_nonsense left in 1.0.0
    (repo / "tmp_output").mkdir()
    for name in ("counts.csv", "script.R", "params_in.json", "stdout", "stderr"):
        (repo / "tmp_output" / name).write_text("")
    assert untracked_files(repo) == {
        "tmp_output/counts.csv",
        "tmp_output/script.R",
        "tmp_output/params_in.json",
        "tmp_output/stdout",
        "tmp_output/stderr",
    }


def test_ignored_and_modified_files_are_not_counted(repo):
    (repo / ".coverage").write_text("")
    (repo / "tracked.txt").write_text("changed\n")
    assert untracked_files(repo) == set()


def test_outside_a_git_work_tree_the_guard_is_off(tmp_path):
    assert untracked_files(tmp_path) is None


def test_inside_another_repository_the_guard_is_off(repo):
    # an unpacked sdist or a copy inside another checkout: git would report on
    # the enclosing repository, which is not this project's
    sub = repo / "sub"
    sub.mkdir()
    (sub / "pyproject.toml").write_text("")
    (repo / "someone_else.txt").write_text("")
    assert untracked_files(sub) is None
    assert files_left_behind(sub, untracked_files(sub)) == []


def test_a_new_file_is_left_behind_and_one_there_before_is_not(repo):
    (repo / "wip.txt").write_text("")
    before = untracked_files(repo)
    (repo / "tmp_output").mkdir()
    (repo / "tmp_output" / "script.R").write_text("")
    assert files_left_behind(repo, before) == ["tmp_output/script.R"]


def test_git_failing_at_the_end_turns_the_guard_off_with_a_warning(repo, monkeypatch):
    before = untracked_files(repo)
    (repo / "left.txt").write_text("")
    monkeypatch.setenv("PATH", "")  # git is gone
    with pytest.warns(UserWarning, match="git status failed"):
        assert files_left_behind(repo, before) == []
