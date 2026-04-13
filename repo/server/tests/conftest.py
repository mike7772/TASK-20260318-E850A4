import pytest
from tests.core.test_lifecycle import setup_session, teardown_session, reset_between_tests


@pytest.fixture(scope="session", autouse=True)
def _session_lifecycle():
    setup_session()
    yield
    teardown_session()


@pytest.fixture(autouse=True)
def _per_test_reset():
    reset_between_tests()
    yield

