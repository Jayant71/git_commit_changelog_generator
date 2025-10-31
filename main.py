"""
AI Agent for generating changelogs from git commits.
"""
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from tools import (
    get_commit_changes, get_commit_summary, get_commit_stats,
    get_staged_changes, get_staged_changes_summary, get_staged_changes_stats,
    set_repo_path, get_repo_path
)

# Load environment variables from .env file
load_dotenv()


def extract_markdown_from_content(content):
    """
    Extract markdown content from LangGraph AI message content.
    Handles both string content and list of content blocks with different types.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        markdown_parts = []
        for block in content:
            if isinstance(block, dict):
                block_type = block.get('type', '')
                block_text = block.get('text', '')

                if block_type == 'text':
                    markdown_parts.append(block_text)
                elif block_type == 'code':
                    language = block.get('language', '')
                    code_text = block.get('text', '')
                    # Format as markdown code block
                    if language:
                        markdown_parts.append(
                            f"```{language}\n{code_text}\n```")
                    else:
                        markdown_parts.append(f"```\n{code_text}\n```")
                else:
                    # For any other type, just include the text
                    markdown_parts.append(str(block.get('text', block)))
            elif hasattr(block, 'type') and hasattr(block, 'text'):
                # Handle objects with type and text attributes
                if block.type == 'text':
                    markdown_parts.append(block.text)
                elif block.type == 'code':
                    language = getattr(block, 'language', '')
                    code_text = block.text
                    if language:
                        markdown_parts.append(
                            f"```{language}\n{code_text}\n```")
                    else:
                        markdown_parts.append(f"```\n{code_text}\n```")
                else:
                    markdown_parts.append(str(block.text))
            else:
                # Fallback: convert to string
                markdown_parts.append(str(block))

        return '\n\n'.join(markdown_parts)

    # Fallback: convert to string
    return str(content)


def setup_agent(for_staged=False):
    """
    Set up the LangGraph AI agent with Gemini model and git tools.
    """
    # Initialize Gemini model
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        temperature=0.7,
    )

    # Define tools based on whether analyzing staged changes or commits
    if for_staged:
        tools = [get_staged_changes, get_staged_changes_summary,
                 get_staged_changes_stats]
        system_prompt = """You are a helpful AI assistant specialized in analyzing git staged changes and generating comprehensive changelogs.

Your task is to:
1. Fetch staged changes information (changes that are added but not yet committed)
2. Analyze the changes that are ready to be committed
3. Generate a well-structured changelog in markdown format that includes:
   - Clear description of what changed
   - List of files modified with their status (added, modified, deleted)
   - Summary of additions/deletions
   - Impact and purpose of the changes
   - Suggestions for commit message if appropriate

Be concise but thorough. Use proper markdown formatting."""
    else:
        tools = [get_commit_changes, get_commit_summary, get_commit_stats]
        system_prompt = """You are a helpful AI assistant specialized in analyzing git commits and generating comprehensive changelogs.

Your task is to:
1. Fetch commit information using the provided commit ID
2. Analyze the changes made in the commit
3. Generate a well-structured changelog in markdown format that includes:
   - Commit ID and metadata (author, date)
   - Clear description of what changed
   - List of files modified
   - Summary of additions/deletions
   - Impact and purpose of the changes

Be concise but thorough. Use proper markdown formatting."""

    # Create agent with memory using LangGraph
    memory = MemorySaver()
    agent = create_agent(
        llm,
        tools,
        checkpointer=memory,
        system_prompt=system_prompt
    )

    return agent


def save_changelog(identifier: str, changelog_content, is_staged=False):
    """
    Save the generated changelog to a markdown file.

    Args:
        identifier: The commit ID or identifier for the changelog
        changelog_content: The changelog content to save (will be converted to string)
        is_staged: Whether this is for staged changes (uncommitted)
    """
    # Ensure content is properly formatted as markdown string
    if isinstance(changelog_content, str):
        content_str = changelog_content
    else:
        content_str = extract_markdown_from_content(changelog_content)

    # Create Changelogs directory if it doesn't exist
    changelogs_dir = Path("Changelogs")
    changelogs_dir.mkdir(exist_ok=True)

    # Save changelog with appropriate filename
    if is_staged:
        # For staged changes, use timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = changelogs_dir / f"staged_{timestamp}.md"
    else:
        filepath = changelogs_dir / f"{identifier}.md"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content_str)

    print(f"\n✓ Changelog saved to: {filepath}")


def generate_changelog(commit_id: str, repo_path=None):
    """
    Generate a changelog for a specific commit ID.

    Args:
        commit_id: The git commit hash/ID to generate changelog for
        repo_path: Path to the git repository (optional, uses current dir if not provided)
    """
    print(f"\n🚀 Generating changelog for commit: {commit_id}")
    if repo_path:
        print(f"📁 Repository: {repo_path}\n")
    else:
        print(f"📁 Repository: Current directory\n")

    # Set up agent
    agent = setup_agent()

    # Run agent to generate changelog
    user_query = f"""Generate a comprehensive changelog for commit ID: {commit_id}

Please:
1. Fetch the commit information
2. Analyze all changes made
3. Create a well-structured markdown changelog

Format the changelog with proper markdown syntax including headers, lists, and code blocks where appropriate."""

    try:
        # Invoke agent with LangGraph pattern
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_query}]},
            {"configurable": {"thread_id": f"commit-{commit_id}"}}
        )

        # Extract the final assistant message
        changelog_content = ""
        for msg in result["messages"]:
            if hasattr(msg, "role") and msg.role == "assistant":
                changelog_content = extract_markdown_from_content(msg.content)
            elif msg.__class__.__name__ == "AIMessage" and msg.content:
                changelog_content = extract_markdown_from_content(msg.content)

        print("\n" + "="*80)
        print("Generated Changelog:")
        print("="*80)
        print(changelog_content)
        print("="*80)

        # Save changelog
        save_changelog(commit_id, changelog_content)

        return changelog_content
    except Exception as e:
        print(f"Error generating changelog: {str(e)}")
        return None


def generate_changelog_for_staged(repo_path=None):
    """
    Generate a changelog for staged changes (uncommitted changes).

    Args:
        repo_path: Path to the git repository (optional, uses current dir if not provided)
    """
    print(f"\n🚀 Generating changelog for STAGED changes (uncommitted)")
    if repo_path:
        print(f"📁 Repository: {repo_path}\n")
    else:
        print(f"📁 Repository: Current directory\n")

    # Set up agent for staged changes
    agent = setup_agent(for_staged=True)

    # Run agent to generate changelog
    user_query = """Generate a comprehensive changelog for the current STAGED changes (changes that are added but not yet committed).

Please:
1. Fetch the staged changes information
2. Analyze all staged changes
3. Create a well-structured markdown changelog
4. Include suggestions for a good commit message

Format the changelog with proper markdown syntax including headers, lists, and code blocks where appropriate."""

    try:
        # Generate unique thread ID for this staged analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Invoke agent with LangGraph pattern
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_query}]},
            {"configurable": {"thread_id": f"staged-{timestamp}"}}
        )

        # Extract the final assistant message
        changelog_content = ""
        for msg in result["messages"]:
            if hasattr(msg, "role") and msg.role == "assistant":
                changelog_content = extract_markdown_from_content(msg.content)
            elif msg.__class__.__name__ == "AIMessage" and msg.content:
                changelog_content = extract_markdown_from_content(msg.content)

        print("\n" + "="*80)
        print("Generated Changelog (Staged Changes):")
        print("="*80)
        print(changelog_content)
        print("="*80)

        # Save changelog with timestamp
        save_changelog(timestamp, changelog_content, is_staged=True)

        return changelog_content
    except Exception as e:
        print(f"Error generating changelog: {str(e)}")
        return None


def main():
    """
    Main function to run the changelog generator.
    """
    print("="*80)
    print("🤖 AI Changelog Generator")
    print("="*80)

    # Check if GOOGLE_API_KEY is set
    if not os.getenv("GOOGLE_API_KEY"):
        print("\n⚠️  Warning: GOOGLE_API_KEY environment variable not set.")
        print("Please set it with your Google AI API key:")
        print("export GOOGLE_API_KEY='your-api-key-here'  # Linux/Mac")
        print("$env:GOOGLE_API_KEY='your-api-key-here'  # PowerShell")
        return

    # Get repository path
    print("\n" + "="*80)
    repo_path = input(
        "Enter the path to git repository (or press Enter for current directory): ").strip()

    if repo_path:
        repo_path = Path(repo_path).resolve()
        if not repo_path.exists():
            print(f"❌ Error: Path '{repo_path}' does not exist.")
            return
        if not (repo_path / ".git").exists():
            print(f"❌ Error: '{repo_path}' is not a git repository.")
            return
        set_repo_path(str(repo_path))
        print(f"✓ Using repository: {repo_path}")
    else:
        # Check if current directory is a git repo
        if not Path(".git").exists():
            print("❌ Error: Current directory is not a git repository.")
            print("Please provide a valid git repository path.")
            return
        print("✓ Using current directory")

    print("="*80)

    # Ask if user wants to analyze staged changes or a commit
    print("\nWhat would you like to analyze?")
    print("1. Staged changes (uncommitted, ready to commit)")
    print("2. Existing commit (using commit ID)")
    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        # Generate changelog for staged changes
        generate_changelog_for_staged(str(repo_path) if repo_path else None)
    elif choice == "2":
        # Get commit ID
        commit_id = input(
            "\nEnter commit ID to generate changelog for: ").strip()
        if not commit_id:
            print("No commit ID provided. Exiting.")
            return
        generate_changelog(commit_id, str(repo_path) if repo_path else None)
    else:
        print("Invalid choice. Exiting.")
        return

    # Option to generate more changelogs
    while True:
        another = input(
            "\n\nGenerate another changelog? (y/n): ").strip().lower()
        if another == 'y':
            change_repo = input(
                "Use a different repository? (y/n): ").strip().lower()
            if change_repo == 'y':
                new_repo_path = input(
                    "Enter the path to git repository: ").strip()
                if new_repo_path:
                    new_repo_path = Path(new_repo_path).resolve()
                    if not new_repo_path.exists() or not (new_repo_path / ".git").exists():
                        print(f"❌ Error: Invalid git repository path.")
                        continue
                    set_repo_path(str(new_repo_path))
                    print(f"✓ Switched to repository: {new_repo_path}")

            # Ask what to analyze
            print("\nWhat would you like to analyze?")
            print("1. Staged changes (uncommitted)")
            print("2. Existing commit")
            choice = input("Enter choice (1 or 2): ").strip()

            if choice == "1":
                current_repo = get_repo_path() if get_repo_path() else None
                generate_changelog_for_staged(current_repo)
            elif choice == "2":
                commit_id = input("Enter commit ID: ").strip()
                if commit_id:
                    current_repo = get_repo_path() if get_repo_path() else None
                    generate_changelog(commit_id, current_repo)
            else:
                print("Invalid choice.")
        else:
            break

    print("\n✓ Done! Thank you for using AI Changelog Generator.")


if __name__ == "__main__":
    main()
