from __future__ import annotations

import os

import pytest

from polarion import PolarionClient

REQUIRED_ENV = [
    "POLARION_URL",
    "POLARION_USERNAME",
    # one of PASSWORD or TOKEN must exist
    "POLARION_PROJECT_ID",
]


def _missing_env() -> list[str]:
    missing = [k for k in REQUIRED_ENV if not os.getenv(k)]
    if not (os.getenv("POLARION_PASSWORD") or os.getenv("POLARION_TOKEN")):
        missing.append("POLARION_PASSWORD|POLARION_TOKEN")
    return missing


def pytest_collection_modifyitems(config, items):
    if not items:
        return

    if config.getoption("--run-integration"):
        return

    skip = pytest.mark.skip(reason="integration tests disabled (pass --run-integration)")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run live integration tests against Polarion instance",
    )


@pytest.fixture(scope="session")
def live_client(pytestconfig):
    if not pytestconfig.getoption("--run-integration"):
        pytest.skip("integration disabled")

    missing = _missing_env()
    if missing:
        pytest.skip(f"missing env vars for integration tests: {', '.join(missing)}")

    client = PolarionClient(
        url=os.environ["POLARION_URL"],
        username=os.environ["POLARION_USERNAME"],
        password=os.getenv("POLARION_PASSWORD"),
        token=os.getenv("POLARION_TOKEN"),
        verify_ssl=os.getenv("POLARION_VERIFY_SSL", "true").lower() in {"1", "true", "yes", "on"},
        timeout=float(os.getenv("POLARION_TIMEOUT", "30")),
    )
    try:
        yield client
    finally:
        client.close()


@pytest.fixture(scope="session")
def project_id() -> str:
    return os.environ["POLARION_PROJECT_ID"]
