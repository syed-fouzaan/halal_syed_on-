import requests

# Replace with your API base URL (must be reachable from the internet).
BASE_URL = "https://staging.example.com"


def test_health_endpoint() -> None:
    response = requests.get(f"{BASE_URL}/health", timeout=30)
    assert response.status_code == 200, f"expected 200, got {response.status_code}"


# The test function MUST be called: TestSprite executes this file top to
# bottom, so a defined-but-never-called function would pass vacuously.
test_health_endpoint()
