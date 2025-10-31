# Git Commit Changelog Generator

An AI-powered agent that automatically generates comprehensive changelogs from git commits using Google's Gemini model.

## Features

- 🤖 AI-powered changelog generation using Gemini Flash
- 📝 Analyzes git commits and creates structured markdown changelogs
- ✨ Generate changelogs for staged changes (before committing)
- 🔧 Multiple tools for fetching commit information, diffs, and statistics
- 💾 Automatically saves changelogs to local `Changelogs/` directory
- 🧠 Persistent memory using LangGraph's MemorySaver
- 🔀 Multi-repository support - analyze any git repository on your system
- 🆕 **Built with LangGraph** - Modern agent framework with React pattern

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your Google API key in a `.env` file:

```bash
GOOGLE_API_KEY='your-api-key-here'
```

## Usage

Run the main script:

```bash
python main.py
```

When prompted:

1. **Enter the path to git repository** - You can specify any git repository path on your system, or press Enter to use the current directory
2. **Choose what to analyze**:
   - Option 1: Staged changes (uncommitted changes that are ready to commit)
   - Option 2: Existing commit (using commit ID)
3. **Provide commit ID** (if analyzing existing commit)

The AI agent will:

1. Fetch the commit/staged changes information from the specified repository
2. Analyze the changes
3. Generate a comprehensive changelog
4. Save it as:
   - `Changelogs/<commit-id>.md` for commits
   - `Changelogs/staged_<timestamp>.md` for staged changes

### Analyzing Staged Changes

Before committing your code, you can generate a changelog for your staged changes:

```bash
# Stage your changes first
git add .

# Run the changelog generator
python main.py

# Choose option 1 when prompted
```

This is useful for:

- Reviewing what you're about to commit
- Getting AI suggestions for commit messages
- Documenting changes before finalizing the commit
- Ensuring your changes are well-documented

You can also switch between different repositories during the same session without restarting the program.

## Tools Available

### For Committed Changes:

- **get_commit_changes**: Fetches full commit details and diff
- **get_commit_summary**: Gets commit metadata and files changed
- **get_commit_stats**: Retrieves commit statistics (insertions/deletions)

### For Staged Changes (Uncommitted):

- **get_staged_changes**: Fetches the diff of staged changes
- **get_staged_changes_summary**: Gets summary of staged files and statistics
- **get_staged_changes_stats**: Retrieves detailed statistics of staged changes

The agent intelligently selects the appropriate tools based on whether you're analyzing:

- **get_commit_changes**: Fetches full commit details and diff
- **get_commit_summary**: Gets commit metadata and files changed
- **get_commit_stats**: Retrieves commit statistics (insertions/deletions)

## Project Structure

```
.
├── main.py           # Main agent implementation
├── tools.py          # Git tools for the agent
├── requirements.txt  # Python dependencies
├── README.md         # This file
└── Changelogs/       # Generated changelogs (created automatically)
```

## How It Works

1. User provides a path to any git repository (or uses current directory)
2. User provides a git commit ID from that repository
3. LangChain agent uses available tools to fetch commit information using `git -C <repo_path>` commands
4. Gemini model analyzes the changes and generates a structured changelog
5. Changelog is saved in markdown format with the commit ID as filename

### Multi-Repository Support

The tools use the `git -C <path>` command to execute git operations on any repository, not just the current directory. This allows you to:

- Generate changelogs for any git repository on your system
- Switch between different repositories during the same session
- Keep all changelogs organized in one central location

## Example Output

The generated changelogs include:

- Commit metadata (ID, author, date)
- Description of changes
- List of modified files
- Code statistics
- Impact analysis
