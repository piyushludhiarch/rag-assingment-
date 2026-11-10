"""Single entry point for the Piyush Spare Parts Assistant."""

import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent

AGENT_DEMO_QUESTIONS = [
    "The pump is making a grinding noise and leaking near the seal. Which part do I need?",
    "Do we have the conveyor belt for machine C2 in stock?",
    "How do I replace a motor bearing safely?",
    "What safety checks come before changing a pump seal?",
    "The machine is not working properly.",
    "What is the best cricket bat to buy?",
]


def run_script(script: str, arguments: list[str] | None = None) -> bool:
    command = [sys.executable, script, *(arguments or [])]
    print(f"\n>>> Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=PROJECT_DIR, check=False)
    return result.returncode == 0


def run_groq():
    return run_script("llm.py")


def run_fault_parser():
    return run_script("fault_parser.py")


def run_rag():
    return run_script("rag.py")


def run_agent_demo():
    successful = True
    for question in AGENT_DEMO_QUESTIONS:
        if not run_script("agent.py", [question]):
            successful = False
    return successful


def run_agent_search():
    print("\nType your maintenance question.")
    print("Type 'exit' to return to the menu.\n")

    while True:
        question = input("Your question: ").strip()
        if not question:
            print("Please enter a question.")
            continue
        if question.lower() in ("exit", "quit", "0"):
            return True

        if not run_script("agent.py", [question]):
            return False


def run_tests():
    return run_script("test_agent.py")


def run_all():
    stages = [
        ("Groq connection", run_groq),
        ("Fault parser", run_fault_parser),
        ("Maintenance RAG", run_rag),
        ("Agent demonstrations", run_agent_demo),
        ("Automated tests", run_tests),
    ]

    failed = []
    for name, stage in stages:
        print(f"\n{'=' * 60}\n{name}\n{'=' * 60}")
        if not stage():
            failed.append(name)

    print("\n" + "=" * 60)
    if failed:
        print("Completed with failures:", ", ".join(failed))
        return False

    print("All project stages completed successfully.")
    return True


def print_menu():
    print(
        "\nPiyush Spare Parts Assistant\n"
        "1. Test Groq connection\n"
        "2. Run fault parser\n"
        "3. Run maintenance RAG\n"
        "4. Ask the assistant a custom question\n"
        "5. Run automated tests\n"
        "6. Run the complete project\n"
        "0. Exit"
    )


def main():
    if len(sys.argv) > 1:
        choice = sys.argv[1].strip()
    else:
        print_menu()
        choice = input("Select an option: ").strip()

    actions = {
        "1": run_groq,
        "2": run_fault_parser,
        "3": run_rag,
        "4": run_agent_search,
        "5": run_tests,
        "6": run_all,
    }

    if choice in ("0", "exit", "quit"):
        return 0
    if choice not in actions:
        print("Unknown option. Use a number from 0 to 6.")
        return 2

    return 0 if actions[choice]() else 1


if __name__ == "__main__":
    raise SystemExit(main())
