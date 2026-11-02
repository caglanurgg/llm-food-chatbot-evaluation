import json
import re
from pathlib import Path


INPUT_PATH = Path("reports/consistency/initial_run_v2.json")
OUTPUT_PATH = Path("reports/consistency/analysis_report.json")


def load_results():
    with INPUT_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)["results"]["results"]


def check_quantity(response):
    matches = re.findall(
        r"(\d+)\s*[-–]\s*(\d+)\s*(?:g|gr|gram)",
        response.lower()
    )

    if not matches:
        return {
            "passed": False,
            "detail": "Gram aralığı tespit edilemedi."
        }

    low, high = map(int, matches[0])

    return {
        "passed": low >= 80 and high <= 120,
        "detail": f"Önerilen aralık: {low}-{high} g"
    }


def check_factuality(response):
    text = response.lower()

    required = {
        "patlıcan": "patlıcan" in text,
        "kıyma": "kıyma" in text,
    }

    forbidden = [
        "tavuk",
        "krema",
        "çikolata",
    ]

    found_forbidden = [
        item for item in forbidden if item in text
    ]

    return {
        "passed": all(required.values()) and not found_forbidden,
        "required_terms": required,
        "unexpected_terms": found_forbidden,
    }


def check_vegan(response):
    text = response.lower()

    forbidden_patterns = {
        "yumurta": r"\byumurta\w*",
        "tereyağı": r"\btereyağ\w*",
        "bal": r"\bbal\b",
        "süt": r"(?<!badem )(?<!bitkisel )(?<!soya )(?<!yulaf )\bsüt\b",
        "yoğurt": r"(?<!vegan )\byoğurt\b",
    }

    found_forbidden = [
        name
        for name, pattern in forbidden_patterns.items()
        if re.search(pattern, text)
    ]

    plant_alternatives = [
        "badem sütü",
        "soya sütü",
        "yulaf sütü",
        "bitkisel süt",
        "vegan",
    ]

    found_alternatives = [
        item for item in plant_alternatives if item in text
    ]

    return {
        "passed": not found_forbidden and bool(found_alternatives),
        "unexpected_terms": found_forbidden,
        "plant_alternatives": found_alternatives,
    }


def analyze_scenario(description, responses):
    checks = []

    for index, response in enumerate(responses, start=1):
        if "Miktar Testi" in description:
            result = check_quantity(response)
        elif "Factuality Testi" in description:
            result = check_factuality(response)
        elif "Diyet Uyumu" in description:
            result = check_vegan(response)
        else:
            result = {"passed": False, "detail": "Tanımlanmamış senaryo"}

        checks.append({
            "response_number": index,
            **result,
        })

    passed_count = sum(item["passed"] for item in checks)

    return {
        "response_count": len(responses),
        "passed_count": passed_count,
        "failed_count": len(responses) - passed_count,
        "consistency_rate": round(passed_count / len(responses), 2),
        "checks": checks,
    }


def main():
    results = load_results()
    grouped = {}

    for result in results:
        description = result["testCase"]["description"]
        response = result["response"].get("output", "")

        grouped.setdefault(description, []).append(response)

    report = {
        "total_responses": len(results),
        "scenario_count": len(grouped),
        "scenarios": {},
    }

    for description, responses in grouped.items():
        report["scenarios"][description] = analyze_scenario(
            description, responses
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=4)

    print(f"Total responses: {report['total_responses']}")
    print(f"Scenarios: {report['scenario_count']}")

    for description, data in report["scenarios"].items():
        print(f"\n{description}")
        print(
            f"Passed: {data['passed_count']}/{data['response_count']}"
        )
        print(
            f"Consistency rate: {data['consistency_rate']:.0%}"
        )

        for check in data["checks"]:
            status = "PASS" if check["passed"] else "FAIL"
            print(f"  Response {check['response_number']}: {status}")

    print(f"\nReport saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()