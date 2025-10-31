"""
Git commit tools for fetching commit information and changes.
"""
import subprocess
from typing import Optional
from langchain.tools import tool
from pathlib import Path

# Global variable to store the repository path
_REPO_PATH = None


def set_repo_path(repo_path: str):
    """Set the repository path for git operations."""
    global _REPO_PATH
    _REPO_PATH = str(Path(repo_path).resolve())


def get_repo_path() -> Optional[str]:
    """Get the current repository path."""
    return _REPO_PATH


@tool
def get_commit_changes(commit_id: str) -> str:
    """
    Fetch the changes in a git commit using commit ID.

    Args:
        commit_id: The git commit hash/ID to fetch changes for

    Returns:
        String containing the commit changes including diff, author, date, and message
    """
    try:
        repo_path = get_repo_path()
        git_cmd_base = ['git', '-C', repo_path] if repo_path else ['git']

        # Get commit details (author, date, message)
        commit_info = subprocess.run(
            git_cmd_base + ['show', '--no-patch',
                            '--format=fuller', commit_id],
            capture_output=True,
            text=True,
            check=True
        )

        # Get commit diff
        commit_diff = subprocess.run(
            git_cmd_base + ['show', commit_id],
            capture_output=True,
            text=True,
            check=True
        )

        result = f"""
Commit Information:
{commit_info.stdout}

Changes:
{commit_diff.stdout}
"""
        return result
    except subprocess.CalledProcessError as e:
        return f"Error fetching commit {commit_id}: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_commit_summary(commit_id: str) -> str:
    """
    Get a brief summary of a commit including message, author, and files changed.

    Args:
        commit_id: The git commit hash/ID

    Returns:
        String containing commit summary
    """
    try:
        repo_path = get_repo_path()
        git_cmd_base = ['git', '-C', repo_path] if repo_path else ['git']

        # Get commit message and metadata
        commit_info = subprocess.run(
            git_cmd_base + ['log', '-1',
                            '--format=%H%n%an%n%ae%n%ad%n%s%n%b', commit_id],
            capture_output=True,
            text=True,
            check=True
        )

        # Get list of files changed
        files_changed = subprocess.run(
            git_cmd_base + ['show', '--name-status', '--format=', commit_id],
            capture_output=True,
            text=True,
            check=True
        )

        lines = commit_info.stdout.strip().split('\n')
        result = f"""
Commit ID: {lines[0] if len(lines) > 0 else 'N/A'}
Author: {lines[1] if len(lines) > 1 else 'N/A'} <{lines[2] if len(lines) > 2 else 'N/A'}>
Date: {lines[3] if len(lines) > 3 else 'N/A'}
Subject: {lines[4] if len(lines) > 4 else 'N/A'}

Files Changed:
{files_changed.stdout}
"""
        return result
    except subprocess.CalledProcessError as e:
        return f"Error fetching commit summary {commit_id}: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_commit_stats(commit_id: str) -> str:
    """
    Get statistics about a commit (files changed, insertions, deletions).

    Args:
        commit_id: The git commit hash/ID

    Returns:
        String containing commit statistics
    """
    try:
        repo_path = get_repo_path()
        git_cmd_base = ['git', '-C', repo_path] if repo_path else ['git']

        stats = subprocess.run(
            git_cmd_base + ['show', '--stat', commit_id],
            capture_output=True,
            text=True,
            check=True
        )
        return stats.stdout
    except subprocess.CalledProcessError as e:
        return f"Error fetching commit stats {commit_id}: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_staged_changes() -> str:
    """
    Get the staged changes (changes added to index but not yet committed).
    This analyzes changes that are ready to be committed.

    Returns:
        String containing the staged changes with diff
    """
    try:
        repo_path = get_repo_path()
        git_cmd_base = ['git', '-C', repo_path] if repo_path else ['git']

        # Check if there are any staged changes
        status = subprocess.run(
            git_cmd_base + ['diff', '--cached', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )

        if not status.stdout.strip():
            return "No staged changes found. Please stage your changes using 'git add' first."

        # Get the diff of staged changes
        diff = subprocess.run(
            git_cmd_base + ['diff', '--cached'],
            capture_output=True,
            text=True,
            check=True
        )

        result = f"""
Staged Changes (Ready to Commit):

{diff.stdout}
"""
        return result
    except subprocess.CalledProcessError as e:
        return f"Error fetching staged changes: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_staged_changes_summary() -> str:
    """
    Get a summary of staged changes including list of files and statistics.

    Returns:
        String containing summary of staged changes
    """
    try:
        repo_path = get_repo_path()
        git_cmd_base = ['git', '-C', repo_path] if repo_path else ['git']

        # Get list of staged files with status
        files_status = subprocess.run(
            git_cmd_base + ['diff', '--cached', '--name-status'],
            capture_output=True,
            text=True,
            check=True
        )

        if not files_status.stdout.strip():
            return "No staged changes found."

        # Get statistics
        stats = subprocess.run(
            git_cmd_base + ['diff', '--cached', '--stat'],
            capture_output=True,
            text=True,
            check=True
        )

        # Get current branch
        branch = subprocess.run(
            git_cmd_base + ['branch', '--show-current'],
            capture_output=True,
            text=True,
            check=True
        )

        result = f"""
Staged Changes Summary:
Branch: {branch.stdout.strip()}

Files Status:
{files_status.stdout}

Statistics:
{stats.stdout}
"""
        return result
    except subprocess.CalledProcessError as e:
        return f"Error fetching staged changes summary: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_staged_changes_stats() -> str:
    """
    Get detailed statistics about staged changes (insertions, deletions, files changed).

    Returns:
        String containing statistics of staged changes
    """
    try:
        repo_path = get_repo_path()
        git_cmd_base = ['git', '-C', repo_path] if repo_path else ['git']

        # Get statistics with numstat for detailed line changes
        numstat = subprocess.run(
            git_cmd_base + ['diff', '--cached', '--numstat'],
            capture_output=True,
            text=True,
            check=True
        )

        if not numstat.stdout.strip():
            return "No staged changes found."

        # Get overall stats
        stats = subprocess.run(
            git_cmd_base + ['diff', '--cached', '--stat'],
            capture_output=True,
            text=True,
            check=True
        )

        result = f"""
Staged Changes Statistics:

Detailed Line Changes:
{numstat.stdout}

Summary:
{stats.stdout}
"""
        return result
    except subprocess.CalledProcessError as e:
        return f"Error fetching staged changes stats: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"
