import json
import sys
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.dataset_loader import validate_dataset as validate_dataset_structure

DATASET_PATH = PROJECT_ROOT / "datasets" / "golden_dataset.json"

SOURCE_FILES = [
    ("FACT", "factuality", "configs/factuality_tests/recipe_ingredient_hallucination.suite.yaml"),
    ("QTY", "quantity", "configs/llm_rubric_tests/quantity_and_portion_bounds.suite.yaml"),
    ("DIET", "dietary", "configs/llm_rubric_tests/dietary_restriction_compliance.suite.yaml"),
    ("BIAS", "bias", "configs/bias_tests/gender_bias_and_stereotypes.suite.yaml"),
    ("SAFE", "safety", "configs/safety_tests/out_of_domain_safety.suite.yaml"),
]


def validate_dataset():
    with DATASET_PATH.open("r", encoding="utf-8-sig") as file:
        dataset = json.load(file)

    # 1. Şema ve yapısal doğrulama (app/dataset_loader kuralları)
    validate_dataset_structure(dataset)

    test_cases = dataset["test_cases"]
    errors = []

    if len(test_cases) != 23:
        errors.append(f"Expected 23 tests, found {len(test_cases)}.")

    # 2. Kaynak YAML dosyaları ile birebir karşılaştırma
    expected_count = 0

    for prefix, category, source in SOURCE_FILES:
        source_path = PROJECT_ROOT / source
        with source_path.open("r", encoding="utf-8-sig") as file:
            source_tests = yaml.safe_load(file)

        category_tests = [
            test for test in test_cases if test.get("source") == source
        ]

        if len(category_tests) != len(source_tests):
            errors.append(
                f"{source}: expected {len(source_tests)} tests, found {len(category_tests)}."
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

            # Temel alanlar
            if generated.get("category") != category:
                errors.append(f"{test_id}: category does not match source.")
            if generated.get("description") != original["description"]:
                errors.append(f"{test_id}: description does not match source.")
            if generated.get("input") != original["vars"]["input"]:
                errors.append(f"{test_id}: input does not match source.")

            # Çoklu evaluations listesi kontrolü
            original_assertions = original.get("assert", [])
            generated_evaluations = generated.get("evaluations", [])

            if len(original_assertions) != len(generated_evaluations):
                errors.append(
                    f"{test_id}: expected {len(original_assertions)} evaluations, "
                    f"found {len(generated_evaluations)}."
                )
                continue

            for eval_idx, (orig_assert, gen_eval) in enumerate(
                zip(original_assertions, generated_evaluations), start=1
            ):
                expected_rubric = orig_assert.get("value", orig_assert.get("rubric", "")).strip()
                expected_type = orig_assert.get("type")
                # Safety testlerinde threshold tanımlanmamışsa varsayılan 0.95 alınmıştı
                expected_threshold = orig_assert.get("threshold", 0.95)

                if gen_eval.get("type") != expected_type:
                    errors.append(f"{test_id} [eval {eval_idx}]: type does not match source.")
                if gen_eval.get("rubric") != expected_rubric:
                    errors.append(f"{test_id} [eval {eval_idx}]: rubric does not match source.")
                if gen_eval.get("threshold") != expected_threshold:
                    errors.append(f"{test_id} [eval {eval_idx}]: threshold does not match source.")

    if expected_count != len(test_cases):
        errors.append("Source and dataset total counts do not match.")

    # 3. Negatif test etiket kontrolü
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
    print(f"Unique IDs: {len({test['id'] for test in test_cases})}")
    print("Evaluation type: llm-rubric")
    print("Source comparison: all fields and evaluations match")
    print("Negative test tags: verified")


if __name__ == "__main__":
    validate_dataset()