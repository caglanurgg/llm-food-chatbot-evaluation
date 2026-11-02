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
    assert test_case["evaluation"]["rubric"]
    assert 0 <= test_case["evaluation"]["threshold"] <= 1
    