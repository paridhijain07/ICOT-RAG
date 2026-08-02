import requests
import urllib3

from rag_icot.components.text_cleaner import TextCleaner


urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


class VARIoTLoader:

    VULNS_URL = "https://www.variotdbs.pl/api/vulns/"
    EXPLOITS_URL = "https://www.variotdbs.pl/api/exploits/"

    def __init__(self):

        self.cleaner = TextCleaner()

    def _get_page(self, url, params):

        response = requests.get(
            url,
            params=params,
            verify=False,
            timeout=60
        )

        response.raise_for_status()

        return response.json()

    def _paginate(
        self,
        url,
        limit=100,
        max_records=500
    ):

        results = []
        offset = 0

        while len(results) < max_records:

            page_limit = min(
                limit,
                max_records - len(results)
            )

            data = self._get_page(
                url,
                {
                    "limit": page_limit,
                    "offset": offset
                }
            )

            page = data.get("results", [])

            if not page:
                break

            results.extend(page)

            if not data.get("next"):
                break

            offset += len(page)

        return results

    def _extract_products(self, value):

        if value is None:
            return []

        if isinstance(value, list):
            products = []

            for item in value:
                if isinstance(item, dict):
                    name = (
                        item.get("name")
                        or item.get("product")
                        or item.get("data")
                        or ""
                    )
                    products.append(
                        self.cleaner.extract_field(name)
                    )
                else:
                    products.append(
                        self.cleaner.extract_field(item)
                    )

            return [p for p in products if p]

        text = self.cleaner.extract_field(value)

        if not text:
            return []

        return [text]

    def normalize_vulnerability(self, raw):

        title = self.cleaner.clean(
            raw.get("title"),
            max_length=300
        )

        description = self.cleaner.clean(
            raw.get("description"),
            max_length=3000
        )

        products = self._extract_products(
            raw.get("affected_products")
            or raw.get("products")
        )

        return {
            "variot_id": raw.get("id") or raw.get("variot_id"),
            "cve": raw.get("cve") or "",
            "title": title,
            "description": description,
            "threat_type": self.cleaner.extract_field(
                raw.get("threat_type")
            ),
            "affected_products": products,
            "document_type": "vulnerability"
        }

    def normalize_exploit(self, raw):

        title = self.cleaner.clean(
            raw.get("title"),
            max_length=300
        )

        # Prefer short advisory text over full PoC dump when both exist
        description = self.cleaner.clean(
            raw.get("description") or raw.get("exploit"),
            max_length=2000
        )

        products = self._extract_products(
            raw.get("affected_products")
        )

        return {
            "id": raw.get("id"),
            "title": title,
            "type": self.cleaner.extract_field(
                raw.get("type")
            ),
            "description": description,
            "affected_products": products,
            "references": raw.get("references", []),
            "last_update_date": raw.get(
                "last_update_date",
                ""
            ),
            "document_type": "exploit"
        }

    def get_vulnerabilities(
        self,
        limit=100,
        max_records=500,
        normalize=True
    ):

        raw_results = self._paginate(
            self.VULNS_URL,
            limit=limit,
            max_records=max_records
        )

        if not normalize:
            return raw_results

        records = [
            self.normalize_vulnerability(item)
            for item in raw_results
        ]

        return [
            record for record in records
            if record["title"] or record["description"]
        ]

    def get_exploits(
        self,
        limit=100,
        max_records=500,
        normalize=True
    ):

        raw_results = self._paginate(
            self.EXPLOITS_URL,
            limit=limit,
            max_records=max_records
        )

        if not normalize:
            return raw_results

        records = [
            self.normalize_exploit(item)
            for item in raw_results
        ]

        return [
            record for record in records
            if record["title"] or record["description"]
        ]
