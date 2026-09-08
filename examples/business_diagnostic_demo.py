"""
Local execute demo for monitoring/business_diagnostic.

Runs the deterministic scenario ledger entirely offline against the in-bundle
fixtures: adjudicate the demo framework against one recorded observation,
calibrate the same marks against a resolved outcome, and one fail-closed
contract error from the closed registry. No API keys, no network, no clock.
"""

import json
from pathlib import Path

from skillware.core.loader import SkillLoader


def _bundle_dir(module) -> Path:
    return Path(module.__file__).resolve().parent


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _print_result(result: dict) -> None:
    print(f"  status: {result['status']}")
    if result["status"] != "completed":
        error = result["error"]
        print(f"  contract error: {error['code']} (fail-closed)")
        print(f"  detail: {error['detail']}")
        return
    for row in result["scenarios"]:
        line = f"  {row['id']}: operator_mark={row['operator_mark']}"
        if "model_implied" in row:
            line += f" model_implied={row['model_implied']} delta={row['delta']}"
        if row["fired"]:
            line += f" fired={row['fired']}"
        print(line)
    calibration = result["calibration"]
    print(
        f"  next_remark_due: {calibration['next_remark_due']}"
        f" days_to_adjudication: {calibration['days_to_adjudication']}"
        f" marks_stale: {result['marks_stale']}"
    )
    if calibration["brier"] is not None:
        print(f"  brier: {calibration['brier']}")
    if result["insufficient_data"]:
        for item in result["insufficient_data"]:
            print(f"  insufficient_data: {item['reason']}")


def run_demo() -> None:
    print("Loading monitoring/business_diagnostic...")
    bundle = SkillLoader.load_skill("monitoring/business_diagnostic")
    skill = bundle["class"]()
    fixtures = _bundle_dir(bundle["module"]) / "fixtures"

    print("\nScenario 1: adjudicate the demo framework against one observation")
    _print_result(
        skill.execute(_load_json(fixtures / "example_adjudicate_params.json"))
    )

    print("\nScenario 2: calibrate the same marks against the resolved outcome")
    _print_result(skill.execute(_load_json(fixtures / "example_calibrate_params.json")))

    print("\nScenario 3: undeclared indicator id (fail-closed contract error)")
    _print_result(
        skill.execute(_load_json(fixtures / "error_unknown_indicator_id.json"))
    )

    print("\nDemo complete.")


if __name__ == "__main__":
    run_demo()
