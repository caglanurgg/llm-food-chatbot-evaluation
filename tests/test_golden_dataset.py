import pytest

from app.dataset_loader import load_dataset


TEST_CASES = load_dataset()["test_cases"]


@pytest.mark.parametrize(
    "test_case",
    TEST_CASES,
    ids=lambda test_case: test_case["id"]
)
def test_golden_dataset_test_cases_are_valid(test_case):
    assert test_case["id"]
    assert test_case["input"]
    assert isinstance(test_case["evaluations"], list)
    assert len(test_case["evaluations"]) > 0

    for evaluation in test_case["evaluations"]:
        assert evaluation["type"] == "llm-rubric"
        assert evaluation["rubric"].strip()
        assert 0 <= evaluation["threshold"] <= 1