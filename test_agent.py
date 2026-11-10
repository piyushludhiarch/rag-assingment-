import json
from pathlib import Path

import agent

QUESTIONS = [
    "The pump is making a grinding noise and leaking near the seal. Which part do I need?",
    "Do we have the conveyor belt for machine C2 in stock?",
    "How do I replace a motor bearing safely?",
    "What safety checks come before changing a pump seal?",
    "The machine is not working properly.",
    "What is the best cricket bat to buy?",
]


def run_tests() -> list[dict]:
    records = []
    for question in QUESTIONS:
        result = agent.run_agent(question, rag=None)
        if question == QUESTIONS[4]:
            correct = "more detail" in result["answer"].lower()
        elif question == QUESTIONS[5]:
            correct = "only" in result["answer"].lower() or "maintenance" in result["answer"].lower()
        else:
            correct = bool(result["answer"])
        records.append({
            "question": question,
            "tool_used": result["tool_used"],
            "correct": correct,
            "answer": result["answer"],
        })
    return records


if __name__ == "__main__":
    results = run_tests()
    Path("test_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
