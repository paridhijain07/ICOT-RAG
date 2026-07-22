import requests


class VARIoTLoader:

    def get_vulnerabilities(self, limit=10):

        url = f"https://www.variotdbs.pl/api/vulns/?limit={limit}"

        response = requests.get(
            url,
            verify=False
        )

        data = response.json()

        return data["results"]