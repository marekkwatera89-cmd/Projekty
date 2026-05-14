import requests
import csv
import gzip
import io

# =========================================================
# KONFIGURACJA
# =========================================================

DOJO_URL = "http://IP:8080"
API_TOKEN = "TOKEN"

HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

EPSS_URL = "https://epss.cyentia.com/epss_scores-current.csv.gz"

# =========================================================
# POBRANIE EPSS
# =========================================================

print("Pobieram EPSS...")

response = requests.get(EPSS_URL, timeout=60)

print("Status EPSS:", response.status_code)

response.raise_for_status()

gzip_file = io.BytesIO(response.content)

epss_data = {}

with gzip.open(gzip_file, 'rt') as f:

    reader = csv.reader(f)

    next(reader)

    count = 0

    for row in reader:

        cve = row[0].strip()

        epss_data[cve] = {
            "epss": row[1],
            "percentile": row[2]
        }

        count += 1

print("Załadowano rekordów EPSS:", count)

# =========================================================
# POBRANIE FINDINGS
# =========================================================

print("Pobieram findings z DefectDojo...")

all_findings = []

url = f"{DOJO_URL}/api/v2/findings/?active=true&limit=100"

while url:

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=60
    )

    print("Status DefectDojo:", response.status_code)

    response.raise_for_status()

    data = response.json()

    results = data.get("results", [])

    all_findings.extend(results)

    print("Pobrano findings:", len(all_findings))

    url = data.get("next")

print("Łącznie findings:", len(all_findings))

# =========================================================
# AKTUALIZACJA
# =========================================================

updated = 0
matched = 0
errors = 0

print("Rozpoczynam aktualizację findings...")

for finding in all_findings:

    finding_id = finding.get("id")

    cves = finding.get("vulnerability_ids", [])

    if not cves:
        continue

    print("\nFinding ID:", finding_id)
    print("CVEs:", cves)

    for cve_item in cves:

        # FORMAT:
        # {'vulnerability_id': 'CVE-2016-2781'}

        if isinstance(cve_item, dict):
            cve = cve_item.get("vulnerability_id")
        else:
            cve = str(cve_item)

        if not cve:
            continue

        print("Sprawdzam CVE:", cve)

        if cve in epss_data:

            matched += 1

            epss = epss_data[cve]["epss"]
            percentile = epss_data[cve]["percentile"]

            print("MATCH:", cve)
            print("EPSS:", epss)
            print("Percentile:", percentile)

            patch_data = {
                "epss_score": epss,
                "epss_percentile": percentile
            }

            try:

                patch_response = requests.patch(
                    f"{DOJO_URL}/api/v2/findings/{finding_id}/",
                    json=patch_data,
                    headers=HEADERS,
                    timeout=60
                )

                print(
                    f"PATCH status: {patch_response.status_code}"
                )

                if patch_response.status_code in [200, 202]:

                    print("UPDATED OK")
                    updated += 1

                else:

                    print("PATCH ERROR:")
                    print(patch_response.text)

                    errors += 1

            except Exception as e:

                print("PATCH EXCEPTION:", e)

                errors += 1

# =========================================================
# PODSUMOWANIE
# =========================================================

print("\n=================================")
print("KONIEC")
print("=================================")
print("MATCHED:", matched)
print("UPDATED:", updated)
print("ERRORS:", errors)
print("=================================")
