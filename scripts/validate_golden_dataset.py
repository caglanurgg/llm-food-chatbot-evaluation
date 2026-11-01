import json
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "datasets" / "golden_dataset.json"

SOURCE_FILES = [
    ("FACT", "factuality", "configs/factuality_tests/recipe_ingredient_hallucination.suite.yaml"),
    ("QTY", "quantity", "configs/llm_rubric_tests/quantity_and_portion_bounds.suite.yaml"),
    ("DIET", "dietary", "configs/llm_rubric_tests/dietary_restriction_compliance.suite.yaml"),
    ("BIAS", "bias", "configs/bias_tests/gender_bias_and_stereotypes.suite.yaml"),
]


def validate_dataset():
    with DATASET_PATH.open("r", encoding="utf-8-sig") as file:
        dataset = json.load(file)

    test_cases = dataset.get("test_cases")

    if not isinstance(test_cases, list):
        raise ValueError("Dataset must contain a test_cases list.")

    errors = []

    # 1. Test sayısı
    if len(test_cases) != 17:
        errors.append(f"Expected 17 tests, found {len(test_cases)}.")

    # 2. ID benzersizliği
    ids = [test.get("id") for test in test_cases]

    if len(ids) != len(set(ids)):
        errors.append("Duplicate test IDs found.")

    # 3. Gerekli alanlar
    required_fields = {
        "id",
        "category",
        "description",
        "input",
        "evaluation",
        "tags",
        "source"
    }

    for test in test_cases:
        missing = required_fields - test.keys()

        if missing:
            errors.append(
                f"{test.get('id', 'Unknown')}: missing fields {sorted(missing)}"
            )
            continue

        evaluation = test["evaluation"]

        if not isinstance(evaluation, dict):
            errors.append(f"{test['id']}: evaluation must be an object.")
            continue

        if evaluation.get("type") != "llm-rubric":
            errors.append(f"{test['id']}: unexpected evaluation type.")

        if not evaluation.get("rubric"):
            errors.append(f"{test['id']}: rubric is missing.")

        threshold = evaluation.get("threshold")

        if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
            errors.append(f"{test['id']}: invalid threshold.")

        if not isinstance(test["tags"], list):
            errors.append(f"{test['id']}: tags must be a list.")

    # 4. Kaynak YAML ile birebir karşılaştırma
    expected_count = 0

    for prefix, category, source in SOURCE_FILES:
        source_path = PROJECT_ROOT / source

        with source_path.open("r", encoding="utf-8-sig") as file:
            source_tests = yaml.safe_load(file)

        category_tests = [
            test for test in test_cases
            if test.get("source") == source
        ]

        if len(category_tests) != len(source_tests):
            errors.append(
                f"{source}: expected {len(source_tests)} tests, "
                f"found {len(category_tests)}."
            )
            continue

        expected_count += len(source_tests)

        for index, original in enumerate(source_tests, start=1):
            test_id = f"{prefix}-{index:03d}"

            generated = next(
                (test for test in category_tests if test.get("id") == test_id),
                None
            )

            if generated is None:
                errors.append(f"Missing test ID: {test_id}")
                continue

            assertion = original["assert"][0]

            comparisons = {
                "category": (generated.get("category"), category),
                "description": (
                    generated.get("description"),
                    original["description"]
                ),
                "input": (
                    generated.get("input"),
                    original["vars"]["input"]
                ),
                "rubric": (
                    generated["evaluation"].get("rubric"),
                    assertion["rubric"].strip()
                ),
                "threshold": (
                    generated["evaluation"].get("threshold"),
                    assertion["threshold"]
                ),
                "evaluation type": (
                    generated["evaluation"].get("type"),
                    assertion["type"]
                )
            }

            for field, (actual, expected) in comparisons.items():
                if actual != expected:
                    errors.append(f"{test_id}: {field} does not match source.")

    if expected_count != len(test_cases):
        errors.append("Source and dataset total counts do not match.")

    # 5. Negatif test etiketleri
    for test in test_cases:
        is_negative = "NEGAT" in test["description"].upper()
        has_tag = "negative-test" in test["tags"]

        if is_negative != has_tag:
            errors.append(
                f"{test['id']}: negative-test tag does not match description."
            )

    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print("-", error)
        raise SystemExit(1)

    print("VALIDATION PASSED")
    print(f"Total tests: {len(test_cases)}")
    print(f"Unique IDs: {len(set(ids))}")
    print("Evaluation type: llm-rubric")
    print("Source comparison: all fields match")
    print("Negative test tags: verified")


if __name__ == "__main__":
    validate_dataset()