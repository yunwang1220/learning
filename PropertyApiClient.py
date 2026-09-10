import time
import requests


class PropertyApiClient:

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

    def _get(self, endpoint: str, params=None):

        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):

            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                )

                response.raise_for_status()

                return response.json()

            except requests.RequestException:

                if attempt == self.max_retries - 1:
                    raise

                time.sleep(2 ** attempt)

    def get_properties(self):

        payload = self._get(
            "/properties"
        )

        return payload["data"]

    def get_property(
        self,
        property_id: int
    ):

        return self._get(
            f"/properties/{property_id}"
        )