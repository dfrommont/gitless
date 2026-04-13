import pytest
@pytest.fixture(autouse=True)
def mock_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *args, **kwargs: "")