import json
import re
from pathlib import Path


INPUT_PATH = Path("reports/consistency/initial_run_v2.json")
OUTPUT_PATH = Path("reports/consistency/analysis_report.json")


def load_results():
    with INPUT_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)["results"]["results"]


def extract_quantity(response):
    matches = re.findall(
        r"(\d+)\s*[-–]\s*(\d+)\s*(?:g|gr|gram)",
        response.lower()
    )

    if not matches:
        return {
            "found": False,
            "detail": "Gram aralığı tespit edilemedi."
        }

    low, high = map(int, matches[0])

    return {
        "found": True,
        "min_grams": low,
        "max_grams": high,
    }


def analyze_quantity_variation(responses):
    quantities = []

    for index, response in enumerate(responses, start=1):
        result = extract_quantity(response)
        if result["found"]:
            quantities.append({"response_number": index, **result})

    if not quantities:
        return {
            "extracted_count": 0,
            "detail": "Hiçbir yanıttan miktar çıkarılamadı."
        }

    lower_values = [item["min_grams"] for item in quantities]
    upper_values = [item["max_grams"] for item in quantities]

    return {
        "extracted_count": len(quantities),
        "min_recommended_grams": min(lower_values),
        "max_recommended_grams": max(upper_values),
        "average_lower_bound": round(sum(lower_values) / len(lower_values), 2),
        "average_upper_bound": round(sum(upper_values) / len(upper_values), 2),
        "portion_range_width": round(sum(item["max_grams"] - item["min_grams"] for item in quantities) / len(quantities), 2),
        "response_variation": max(max(lower_values) - min(lower_values), max(upper_values) - min(upper_values)),
        "individual_results": quantities,
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

    if "Miktar Testi 1" in description:
        return {
            "response_count": len(responses),
            "quantity_variation": analyze_quantity_variation(responses),
        }

    for index, response in enumerate(responses, start=1):
        if "Miktar Testi" in description:
            result = extract_quantity(response)
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

    passed_count = sum(item.get("passed", False) for item in checks)

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

        # Miktar analizi senaryoları için KeyError koruması
        if "quantity_variation" in data:
            qv = data["quantity_variation"]
            extracted = qv.get("extracted_count", 0)
            print(f"  Extracted: {extracted}/{data['response_count']}")
            if extracted > 0:
                print(f"  Min - Max: {qv['min_recommended_grams']}g - {qv['max_recommended_grams']}g")
                print(f"  Response variation: {qv['response_variation']}g")
            else:
                print(f"  Detail: {qv.get('detail', 'Veri yok')}")
        else:
            print(
                f"  Passed: {data['passed_count']}/{data['response_count']}"
            )
            print(
                f"  Consistency rate: {data['consistency_rate']:.0%}"
            )

            for check in data.get("checks", []):
                status = "PASS" if check.get("passed") else "FAIL"
                print(f"  Response {check['response_number']}: {status}")

    print(f"\nReport saved: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()