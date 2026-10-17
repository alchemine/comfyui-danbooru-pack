"""Offline: Danbooru responses are faked, nothing is sent."""

import types


def test_auth_is_sent_when_login_and_key_are_set(nodes, monkeypatch):
    monkeypatch.setenv("DANBOORU_LOGIN", "fennec")
    monkeypatch.setenv("DANBOORU_API_KEY", "key")
    assert nodes.BaseDanbooru.get_auth() == ("fennec", "key")


def test_no_auth_without_api_key(nodes, monkeypatch):
    monkeypatch.setenv("DANBOORU_LOGIN", "fennec")
    monkeypatch.delenv("DANBOORU_API_KEY", raising=False)
    assert nodes.BaseDanbooru.get_auth() is None


def fake_pages(nodes, monkeypatch, pages):
    def get_json(url, ttl=None):
        page = int(url.rsplit("page=", 1)[1])
        return pages[page - 1] if page <= len(pages) else []

    monkeypatch.setattr(
        nodes.DanbooruPostsDownloader, "_get_json", staticmethod(get_json)
    )


def test_posts_without_a_file_are_replaced_from_the_next_page(nodes, monkeypatch):
    post = lambda i: {"id": i, "file_url": f"https://cdn.donmai.us/{i}.jpg"}
    fake_pages(nodes, monkeypatch, [[post(3), {"id": 2}], [post(1)]])
    assert [d["id"] for d in nodes.DanbooruPostsDownloader.request("x", n=2)] == [3, 1]


def test_request_stops_when_the_search_runs_out(nodes, monkeypatch):
    fake_pages(nodes, monkeypatch, [[{"id": 2}]])
    assert nodes.DanbooruPostsDownloader.request("x", n=1) == []


def test_file_is_named_by_post_id_and_not_downloaded_twice(
    nodes, output_dir, monkeypatch
):
    fake_pages(
        nodes, monkeypatch, [[{"id": 42, "file_url": "https://cdn.donmai.us/a.png"}]]
    )
    calls = []
    session = types.SimpleNamespace(
        get=lambda *a, **k: (
            calls.append(a) or types.SimpleNamespace(ok=True, content=b"png")
        )
    )
    monkeypatch.setattr(nodes, "_get_session", lambda: session)
    run = lambda: nodes.DanbooruPostsDownloader.execute(
        tags="x", n=1, dir_path="issue8", prefix="p"
    )
    assert run() == (["issue8/p_42.png"],)
    assert run() == (["issue8/p_42.png"],)
    assert len(calls) == 1
