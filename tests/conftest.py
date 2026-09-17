"""Test fixtures: the pack imported as ComfyUI would, with the network faked.

`folder_paths` (a ComfyUI module) is stubbed so the pack imports outside
ComfyUI, and every HTTP call goes through `FakeSession`, so no test ever
reaches danbooru.donmai.us.
"""

import sys
import types
import importlib
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parent.parent
PACK_NAME = "danbooru_pack"


class FakeResponse:
    def __init__(self, payload=None, status_code=200, content=b""):
        self._payload = payload
        self.status_code = status_code
        self.content = content
        self.text = "" if payload is None else repr(payload)

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        return self._payload


class FakeSession:
    """Routes a URL to a canned response; records every GET it serves.

    `routes` maps a URL to a payload (JSON), a `FakeResponse`, or an exception
    instance to raise. `default` is the response for an unknown URL.
    """

    def __init__(self, routes=None, default=None):
        self.routes = dict(routes or {})
        self.default = default
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        hit = self.routes.get(url, self.default)
        if isinstance(hit, Exception):
            raise hit
        if isinstance(hit, FakeResponse):
            return hit
        if hit is None:
            return FakeResponse(payload={"error": "not routed"}, status_code=404)
        return FakeResponse(payload=hit)


@pytest.fixture(scope="session")
def pack(tmp_path_factory):
    """The pack registered as an importable package, with `folder_paths` stubbed.

    Registered under a fixed alias rather than the directory name so the test
    run does not depend on how the checkout is named.
    """
    output_dir = tmp_path_factory.mktemp("output")
    stub = types.ModuleType("folder_paths")
    stub.get_output_directory = lambda: str(output_dir)
    sys.modules["folder_paths"] = stub
    package = types.ModuleType(PACK_NAME)
    package.__path__ = [str(PACK_DIR)]
    sys.modules[PACK_NAME] = package
    return package


@pytest.fixture
def mod(pack):
    """The requests-based node module, with its cache cleared."""
    m = importlib.import_module(f"{PACK_NAME}.nodes.danbooru_requests")
    m.BaseDanbooru.REQUEST_CACHE.clear()
    yield m
    m.BaseDanbooru.REQUEST_CACHE.clear()


@pytest.fixture
def session(mod, monkeypatch):
    """Install a FakeSession as the module's pooled session and return it."""
    fake = FakeSession()
    monkeypatch.setattr(mod, "_session", fake)
    return fake


@pytest.fixture
def fake_response():
    return FakeResponse


@pytest.fixture
def output_dir(pack):
    import folder_paths

    return Path(folder_paths.get_output_directory())


@pytest.fixture(autouse=True)
def no_proxy_env(monkeypatch):
    for key in ("WEBSHARE_PROXY_USERNAME", "WEBSHARE_PROXY_PASSWORD", "WEBSHARE_PROXY_SERVER"):
        monkeypatch.delenv(key, raising=False)
