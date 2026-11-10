"""Parse technician notes and search the authoritative parts catalog."""

import json
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

from llm import ask_llm

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def _json_object(text: str) -> Dict[str, str]:
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start:end + 1])
    raise ValueError(f"LLM did not return a JSON object: {text}")


def parse_fault_zero_shot(note: str) -> Dict[str, str]:
    prompt = (
        "Extract the machine, symptom, and part category from the technician note as JSON "
        "with exactly these keys: machine, symptom, part_category. Return JSON only.\n\n"
        f"Note: {note}"
    )
    return _json_object(ask_llm(prompt))


def parse_fault_few_shot(note: str) -> Dict[str, str]:
    examples = (
        'Input: "Lathe spindle is noisy"\n'
        '{"machine":"lathe","symptom":"noisy spindle","part_category":"bearing"}\n'
        'Input: "Mill coolant hose leaks"\n'
        '{"machine":"cnc mill","symptom":"coolant hose leak","part_category":"hose"}\n'
    )
    prompt = (
        "Extract fields as JSON with exactly machine, symptom, and part_category. "
        "Use repair-part language suitable for a catalog search.\n\n"
        + examples
        + f'\nInput: "{note}"\nJSON:'
    )
    return _json_object(ask_llm(prompt))


def find_parts(fault_note: str | Dict[str, str], catalog_path: str | Path | None = None) -> List[dict]:
    """Search pandas data only. Price and stock come exclusively from the catalog."""
    path = Path(catalog_path) if catalog_path else DATA_DIR / "parts_catalog.csv"
    catalog = pd.read_csv(path)
    parsed_fault = parse_fault_few_shot(fault_note) if isinstance(fault_note, str) else fault_note
    machine = str(parsed_fault.get("machine", "")).strip().lower()
    category = str(parsed_fault.get("part_category", "")).strip().lower()
    machine_map = {"pump": "c1", "hydraulic pump": "c1", "motor": "p1", "conveyor": "c2"}
    machine_code = machine_map.get(machine, machine)
    matches = catalog[catalog["category"].str.lower().eq(category)]
    matches = matches[
        matches["compatible_machine"].str.lower().eq(machine_code)
        | matches["compatible_machine"].str.lower().isin([machine])
    ]
    return matches.to_dict(orient="records")


def compare_prompts(notes: Iterable[dict]) -> List[dict]:
    results = []
    for item in notes:
        zero = parse_fault_zero_shot(item["note"])
        few = parse_fault_few_shot(item["note"])
        results.append({"note": item["note"], "zero_shot": zero, "few_shot": few})
    return results


if __name__ == "__main__":
    notes = pd.read_csv(DATA_DIR / "fault_notes.csv").to_dict(orient="records")
    notes = [item for item in notes if item["machine"].strip().lower() != "unknown"][:5]
    print(json.dumps(compare_prompts(notes), indent=2))
