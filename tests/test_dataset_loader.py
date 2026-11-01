import pytest

from app.dataset_loader import load_dataset, validate_dataset


def create_valid_test_case():
    return {
        "id": "TEST-001",
        "category": "factuality",
        "description": "Test description",
        "input": "Test prompt",
        "evaluation": {
            "type": "llm-rubric",
            "rubric": "The answer must be factually correct.",
            "threshold": 0.9
        },
        "tags": ["factuality"],
        "source": "test_source.yaml"
    }


def test_load_dataset_successfully():
    dataset = load_dataset()

    assert "test_cases" in dataset
    assert len(dataset["test_cases"]) == 17


def test_validate_dataset_rejects_missing_fields():
    test_case = create_valid_test_case()
    del test_case["description"]

    dataset = {"test_cases": [test_case]}

    with pytest.raises(ValueError, match="missing fields"):
        validate_dataset(dataset)


def test_validate_dataset_rejects_duplicate_ids():
    first_case = create_valid_test_case()
    second_case = create_valid_test_case()

    dataset = {
        "test_cases": [first_case, second_case]
    }

    with pytest.raises(ValueError, match="Duplicate test case ID"):
        validate_dataset(dataset)


def test_validate_dataset_rejects_invalid_evaluation_type():
    test_case = create_valid_test_case()
    test_case["evaluation"]["type"] = "unknown"

    dataset = {"test_cases": [test_case]}

    with pytest.raises(ValueError, match="Invalid evaluation type"):
        validate_dataset(dataset)


def test_validate_dataset_rejects_invalid_threshold():
    test_case = create_valid_test_case()
    test_case["evaluation"]["threshold"] = 1.5

    dataset = {"test_cases": [test_case]}

    with pytest.raises(ValueError, match="Invalid threshold"):
        validate_dataset(dataset)