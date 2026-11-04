import json
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "datasets" / "golden_dataset.json"

SOURCE_FILES = [
    ("FACT", "factuality", "configs/factuality_tests/recipe_ingredient_hallucination.suite.yaml"),
    ("QTY", "quantity", "configs/llm_rubric_tests/quantity_and_portion_bounds.suite.yaml"),
    ("DIET", "dietary", "configs/llm_rubric_tests/dietary_restriction_compliance.suite.yaml"),
    ("BIAS", "bias", "configs/bias_tests/gender_bias_and_stereotypes.suite.yaml"),
    ("SAFE", "safety", "configs/safety_tests/out_of_domain_safety.suite.yaml"),
]


def build_dataset():
    test_cases = []
    counters = {}

    for prefix, category, source in SOURCE_FILES:
        source_path = PROJECT_ROOT / source

        with source_path.open("r", encoding="utf-8-sig") as file:
            source_tests = yaml.safe_load(file)

        if not isinstance(source_tests, list):
            raise ValueError(f"Invalid YAML test list: {source}")

        for test in source_tests:
            assertions = test.get("assert", [])
            prompt = test.get("vars", {}).get("input")

            if not prompt:
                raise ValueError(
                    f"Missing input in: {test.get('description')}"
                )

            if not assertions:
                raise ValueError(
                    f"At least one assertion is required in: {test.get('description')}"
                )

            evaluations = []

            for assertion in assertions:
                rubric = assertion.get("value", assertion.get("rubric"))
                threshold = assertion.get("threshold")
                evaluation_type = assertion.get("type")

                if not rubric or threshold is None or not evaluation_type:
                    raise ValueError(
                        f"Missing assertion data in: {test.get('description')}"
                    )

                evaluations.append({
                    "type": evaluation_type,
                    "rubric": rubric.strip(),
                    "threshold": threshold
                })

            counters[prefix] = counters.get(prefix, 0) + 1
            test_id = f"{prefix}-{counters[prefix]:03d}"

            tags = [category]

            if "NEGAT" in test.get("description", "").upper():
                tags.append("negative-test")

            test_cases.append({
                "id": test_id,
                "category": category,
                "description": test["description"],
                "input": prompt,
                "evaluations": evaluations,
                "tags": tags,
                "source": source
            })

    return {
        "dataset_name": "AI Food Chatbot Golden Dataset",
        "version": "1.0.0",
        "test_cases": test_cases
    }


if __name__ == "__main__":
    dataset = build_dataset()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(dataset, file, ensure_ascii=False, indent=2)

    print(f"Golden Dataset created: {OUTPUT_PATH}")
    print(f"Total test cases: {len(dataset['test_cases'])}")