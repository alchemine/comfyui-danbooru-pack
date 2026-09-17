"""Live tests: every test here talks to danbooru.donmai.us.

`folder_paths` (a ComfyUI module) is stubbed so the pack imports outside
ComfyUI; nothing else is faked. If Danbooru is unreachable from this machine
(rate limit, IP block), set the Webshare proxy in `.env` -- the pack reads it.
"""

import sys
import types
import importlib
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parent.parent
PACK_NAME = "danbooru_pack"


@pytest.fixture(scope="session")
def output_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("output")


@pytest.fixture(scope="session")
def nodes(output_dir):
    """The requests-based node module, imported the way ComfyUI would."""
    stub = types.ModuleType("folder_paths")
    stub.get_output_directory = lambda: str(output_dir)
    sys.modules["folder_paths"] = stub
    package = types.ModuleType(PACK_NAME)
    package.__path__ = [str(PACK_DIR)]
    sys.modules[PACK_NAME] = package
    return importlib.import_module(f"{PACK_NAME}.nodes.danbooru_requests")
