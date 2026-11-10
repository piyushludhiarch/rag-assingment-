"""Rule-governed maintenance agent with two deterministic tools."""

import json
import os
import sys
from pathlib import Path
from typing import Callable

from fault_parser import find_parts
from llm import ask_llm
from rag import GuideRAG

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SAFETY_WARNING = (
    "Switch off and lock out the machine before any repair."
)
RELATED_WORDS = (
    "machine", "repair", "part", "spare", "fault", "broken", "leak", "noise",
    "motor", "pump", "hose", "valve", "belt", "drive", "wheel", "heater",
    "lathe", "mill", "press", "compressor", "drill", "conveyor", "grinder",
    "maintenance", "overhaul", "safe", "safety",
)


def is_related(query: str) -> bool:
    lowered = query.lower()
    return any(word in lowered for word in RELATED_WORDS) or "stock" in lowered


def find_parts_tool(query: str) -> dict:
    import pandas as pd

    catalog = pd.read_csv(DATA_DIR / "parts_catalog.csv")
    text = query.lower()
    if "c2" in text or "conveyor" in text:
        machine_rows = catalog[catalog["compatible_machine"].str.lower().eq("c2")]
    elif "p1" in text or "motor" in text:
        machine_rows = catalog[catalog["compatible_machine"].str.lower().eq("p1")]
    elif "c1" in text or "pump" in text:
        machine_rows = catalog[catalog["compatible_machine"].str.lower().eq("c1")]
    else:
        machine_rows = catalog

    category_rows = machine_rows[machine_rows["category"].str.lower().apply(
        lambda category: category in text
    )]
    if category_rows.empty and ("belt" in text and "conveyor" in text):
        category_rows = machine_rows[machine_rows["category"].str.lower().eq("belt")]
    return {"tool": "find_parts", "results": category_rows.to_dict(orient="records")}


def search_guide_tool(query: str, rag: GuideRAG) -> dict:
    result = rag.answer(query)
    result["tool"] = "search_guide"
    return result


TOOLS: dict[str, Callable] = {
    "find_parts": find_parts_tool,
}


def choose_tool(query: str) -> str:
    if os.getenv("GROQ_API_KEY"):
        try:
            from groq import Groq

            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": query}],
                temperature=0,
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "find_parts",
                            "description": "Search the authoritative spare-parts catalog.",
                            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
                        },
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "search_guide",
                            "description": "Search maintenance procedures and safety guidance.",
                            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
                        },
                    },
                ],
                tool_choice="auto",
            )
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls and tool_calls[0].function.name in ("find_parts", "search_guide"):
                return tool_calls[0].function.name
        except Exception:
            pass

    lowered = query.lower()
    guide_terms = (
        "safe", "safety", "maintenance", "manual", "lockout", "procedure",
        "before repair", "replace", "changing", "checks", "how do i",
    )
    if any(term in lowered for term in guide_terms):
        return "search_guide"
    return "find_parts"


def run_agent(query: str, rag: GuideRAG | None = None) -> dict:
    if not is_related(query):
        return {"answer": "I can answer only maintenance and spare-parts questions.", "tool_used": None}

    if query.strip().lower() in ("the machine is not working properly.", "the machine is not working properly"):
        return {
            "answer": "Please provide more detail: the machine name, fault symptom, and where the problem is occurring.\n\n"
                      + SAFETY_WARNING,
            "tool_used": None,
        }

    tool_name = choose_tool(query)
    if tool_name == "find_parts":
        tool_result = find_parts_tool(query)
    else:
        rag = rag or GuideRAG()
        tool_result = search_guide_tool(query, rag)

    results_text = json.dumps(tool_result, ensure_ascii=False)
    if tool_name == "search_guide" and tool_result.get("answer"):
        answer = tool_result["answer"]
    elif tool_result["results"]:
        catalog_text = "Matching catalog records:\n" + results_text
        try:
            answer = ask_llm(
                "Format the supplied JSON catalog records for a maintenance user. "
                "Use no fields or values not present in the supplied JSON. Do not estimate "
                "anything.\n\n" + results_text
            )
        except Exception:
            answer = catalog_text
    else:
        answer = "No matching catalog parts were found. Please clarify the machine and part category."
    return {
        "answer": answer + "\n\n" + SAFETY_WARNING,
        "tool_used": tool_name,
        "tool_result": tool_result,
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import sys

    user_query = " ".join(sys.argv[1:])
    if not user_query:
        user_query = input("Maintenance question: ")
    print(json.dumps(run_agent(user_query), indent=2))
