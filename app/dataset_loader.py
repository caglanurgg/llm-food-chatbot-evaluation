import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "datasets" / "golden_dataset.json"

ALLOWED_EVALUATION_TYPES = {
    "llm-rubric"
}


def load_dataset() -> dict:
    """
    Loads and validates the Golden Dataset.
    """
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Golden Dataset not found: {DATASET_PATH}"
        )

    with DATASET_PATH.open("r", encoding="utf-8-sig") as file:
        dataset = json.load(file)

    validate_dataset(dataset)

    return dataset


def validate_dataset(dataset: dict) -> None:
    """
    Validates the Golden Dataset structure and test case fields.
    """
    if not isinstance(dataset, dict):
        raise ValueError("Dataset must be a JSON object.")

    if not isinstance(dataset.get("test_cases"), list):
        raise ValueError("Dataset must contain a test_cases list.")

    required_fields = {
        "id",
        "category",
        "description",
        "input",
        "evaluations",
        "tags",
        "source"
    }

    seen_ids = set()

    for test_case in dataset["test_cases"]:
        if not isinstance(test_case, dict):
            raise ValueError("Each test case must be a JSON object.")

        missing_fields = required_fields - test_case.keys()

        if missing_fields:
            raise ValueError(
                f"Test case is missing fields: {sorted(missing_fields)}"
            )

        test_id = test_case["id"]

        if not isinstance(test_id, str) or not test_id.strip():
            raise ValueError("Test case ID must be a non-empty string.")

        if test_id in seen_ids:
            raise ValueError(f"Duplicate test case ID: {test_id}")

        seen_ids.add(test_id)

        for field in ("category", "description", "input", "source"):
            if (
                not isinstance(test_case[field], str)
                or not test_case[field].strip()
            ):
                raise ValueError(
                    f"{field} must be a non-empty string in {test_id}."
                )

        evaluations = test_case["evaluations"]

        if not isinstance(evaluations, list) or not evaluations:
            raise ValueError(
                f"Evaluations must be a non-empty list in {test_id}."
            )

        required_evaluation_fields = {
            "type",
            "rubric",
            "threshold"
        }

        for index, evaluation in enumerate(evaluations, start=1):
            if not isinstance(evaluation, dict):
                raise ValueError(
                    f"Each evaluation must be an object in {test_id}."
                )

            missing_evaluation_fields = (
                required_evaluation_fields - evaluation.keys()
            )

            if missing_evaluation_fields:
                raise ValueError(
                    f"Evaluation {index} is missing fields in {test_id}: "
                    f"{sorted(missing_evaluation_fields)}"
                )

            if evaluation["type"] not in ALLOWED_EVALUATION_TYPES:
                raise ValueError(
                    f"Invalid evaluation type in {test_id}."
                )

            if (
                not isinstance(evaluation["rubric"], str)
                or not evaluation["rubric"].strip()
            ):
                raise ValueError(
                    f"Rubric must be a non-empty string in {test_id}."
                )

            threshold = evaluation["threshold"]

            if (
                isinstance(threshold, bool)
                or not isinstance(threshold, (int, float))
                or not 0 <= threshold <= 1
            ):
                raise ValueError(
                    f"Invalid threshold in {test_id}. "
                    "Expected a number between 0 and 1."
                )

        if (
            not isinstance(test_case["tags"], list)
            or not all(
                isinstance(tag, str)
                for tag in test_case["tags"]
            )
        ):
            raise ValueError(
                f"Tags must be a list of strings in {test_id}."
            )