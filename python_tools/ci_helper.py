import os
import autogen

from LLMInfoProvider import get_llm_config

# 1) LLM config

REPO_DIR = os.getenv("REPO_DIR", os.path.abspath("./repo"))  # set in CI or local

# 2) DevExecutor: sees the repo and can execute commands/code
dev_executor = autogen.UserProxyAgent(
    name="dev_executor",
    human_input_mode="NEVER",  # change to "ALWAYS" for interactive approvals
    code_execution_config={
        "work_dir": REPO_DIR,
        "use_docker": False,  # can flip to True if you want isolation
    },
    system_message=(
        "You are a developer operations agent. "
        "You can run shell commands and Python code in the repository workspace. "
        "Use this to run tests, inspect files, and write reports. "
        "ALWAYS print command outputs clearly."
    ),
)

# 3) CodeReviewer agent
code_reviewer = autogen.AssistantAgent(
    name="code_reviewer",
    llm_config=get_llm_config(),
    system_message=(
        "You are a senior code reviewer working on a GitHub repository. "
        "Your goals:\n"
        "- Review changed files (provided via diffs or file contents)\n"
        "- Comment on correctness, design, readability, performance, and security\n"
        "- Suggest specific improvements and refactors\n"
        "- Highlight any potential bugs or risky patterns\n\n"
        "Return a structured review with sections: Summary, Strengths, Issues, "
        "Suggested Changes, and Potential Follow-ups."
    ),
)

# 4) Documentor agent
documentor = autogen.AssistantAgent(
    name="documentor",
    llm_config=get_llm_config(),
    system_message=(
        "You are a documentation specialist. "
        "Given code and project structure, you:\n"
        "- Propose or update docstrings for functions/classes\n"
        "- Generate concise markdown documentation for key modules\n"
        "- Create or update docs/AI_REVIEW.md with:\n"
        "  - Overview of changes\n"
        "  - How to use new/changed APIs\n"
        "  - Any prerequisites or setup steps\n"
        "Focus on clarity and usefulness for future developers."
    ),
)

# 5) TestAgent
test_agent = autogen.AssistantAgent(
    name="test_agent",
    llm_config=get_llm_config(),
    system_message=(
        "You are a test executor and designer. "
        "Your tasks:\n"
        "- Decide how to run tests (prefer pytest if present)\n"
        "- Instruct the dev_executor to run appropriate test commands\n"
        "- Interpret failures from test output\n"
        "- Suggest fixes or new tests if coverage looks weak\n"
        "Prefer commands like `pytest -q` or reading existing test files."
    ),
)

# 6) GroupChat + Manager
groupchat = autogen.GroupChat(
    agents=[dev_executor, code_reviewer, documentor, test_agent],
    messages=[],
    max_round=20,
)

manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config=get_llm_config(),
)

# 7) Task for the system (what it should actually do)
task = f"""
We are in a CI job / local run for a GitHub repository located at: {REPO_DIR}

Goals:
1. Determine the set of recently changed files:
   - Prefer using git commands (e.g., `git diff --name-only HEAD~1` or similar).
2. Run the test suite:
   - If pytest is available, run `pytest -q`.
   - Otherwise, inspect the project and choose a sensible test command.
   - Capture failures and summarize them.
3. Perform a code review of the changed files:
   - The dev_executor can show you diffs or file contents.
   - CodeReviewer should provide a structured review.
4. Generate or update documentation:
   - Documentor should create/append to `docs/AI_REVIEW.md` (create folder if needed)
     with:
       - Overview of the change
       - Any new functions/classes and how to use them
       - Any breaking changes or caveats.

At the end, produce:
- A high-level summary for posting as a PR comment.
- A path to the generated docs file (docs/AI_REVIEW.md).
"""

if __name__ == "__main__":
    dev_executor.initiate_chat(manager, message=task)