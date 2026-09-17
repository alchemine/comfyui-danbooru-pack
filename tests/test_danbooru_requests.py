import requests
import pytest


def post(id_, general="1girl solo", character="", copyright_="", artist="", meta="", file_url=None):
    d = {
        "id": id_,
        "tag_string_general": general,
        "tag_string_character": character,
        "tag_string_copyright": copyright_,
        "tag_string_artist": artist,
        "tag_string_meta": meta,
    }
    if file_url is not None:
        d["file_url"] = file_url
    return d


def related(name, frequency=1.0, cosine=1.0, deprecated=False):
    return {
        "tag": {"name": name, "is_deprecated": deprecated},
        "frequency": frequency,
        "cosine_similarity": cosine,
        "jaccard_similarity": cosine,
        "overlap_coefficient": cosine,
    }


def related_url(query, category="General", order="Frequency"):
    return (
        "https://danbooru.donmai.us/related_tag.json?commit=Search"
        f"&search[category]={category}&search[order]={order}&search[query]={query}"
    )


def popular_url(page, date="", scale="day"):
    params = []
    if date:
        params.append(f"date={date}")
    params.append(f"scale={scale}")
    params.append(f"page={page}")
    return "https://danbooru.donmai.us/explore/posts/popular.json?" + "&".join(params)


#################################################################
# Tag helpers
#################################################################
@pytest.mark.parametrize("tag, expected", [
    ("cat", "cat"),
    ("  cat ", "cat"),
    ("(cat:1.2)", "cat"),
    ("(cat:1.2:1.3)", "cat"),
    ("((cat))", "cat"),
    ("[[cat]]", "cat"),
    ("(cat:-0.5)", "cat"),
    (r"(ray \(arknights\):1.1)", r"ray \(arknights\)"),
])
def test_normalize_and_remove_weight_strip_emphasis(mod, tag, expected):
    assert mod.BaseDanbooru.normalize_tag(tag) == expected
    assert mod.BaseDanbooru.remove_weight(tag) == expected


def test_tag_conversion_round_trips_qualifiers(mod):
    b = mod.BaseDanbooru
    assert b.convert_to_danbooru_tag(r"ray \(arknights\)") == "ray_(arknights)"
    assert b.convert_from_danbooru_tag("ray_(arknights)") == r"ray \(arknights\)"
    assert b.convert_from_danbooru_tag(b.convert_to_danbooru_tag(r"blue eyes")) == "blue eyes"


#################################################################
# Proxy config
#################################################################
def test_no_proxy_without_both_credentials(mod, monkeypatch):
    assert mod.BaseDanbooru.get_proxies() is None
    monkeypatch.setenv("WEBSHARE_PROXY_USERNAME", "u")
    assert mod.BaseDanbooru.get_proxies() is None


def test_proxy_url_embeds_credentials(mod, monkeypatch):
    monkeypatch.setenv("WEBSHARE_PROXY_USERNAME", "u")
    monkeypatch.setenv("WEBSHARE_PROXY_PASSWORD", "p")
    assert mod.BaseDanbooru.get_proxies() == {
        "http": "http://u:p@p.webshare.io:80",
        "https": "http://u:p@p.webshare.io:80",
    }
    monkeypatch.setenv("WEBSHARE_PROXY_SERVER", "proxy.local:8080")
    assert mod.BaseDanbooru.get_proxies()["https"] == "http://u:p@proxy.local:8080"


def test_session_ignores_ambient_proxy_env(mod, monkeypatch):
    monkeypatch.setattr(mod, "_session", None)
    s = mod._get_session()
    assert isinstance(s, requests.Session)
    assert s.trust_env is False
    assert s.headers["User-Agent"].startswith("comfyui-danbooru-pack")


#################################################################
# _get_json: caching and errors
#################################################################
def test_get_json_caches_immutable_endpoint_forever(mod, session):
    session.routes["u"] = {"a": 1}
    assert mod.BaseDanbooru._get_json("u") == {"a": 1}
    assert mod.BaseDanbooru._get_json("u") == {"a": 1}
    assert len(session.calls) == 1


def test_get_json_refetches_volatile_endpoint_after_ttl(mod, session, monkeypatch):
    session.routes["u"] = {"a": 1}
    now = [1000.0]
    monkeypatch.setattr(mod.time, "time", lambda: now[0])
    mod.BaseDanbooru._get_json("u", ttl=60)
    now[0] += 59
    mod.BaseDanbooru._get_json("u", ttl=60)
    assert len(session.calls) == 1
    now[0] += 2
    mod.BaseDanbooru._get_json("u", ttl=60)
    assert len(session.calls) == 2


def test_get_json_raises_on_http_error_and_does_not_cache(mod, session, fake_response):
    session.routes["u"] = fake_response({"error": "nope"}, status_code=429)
    with pytest.raises(Exception, match="status 429"):
        mod.BaseDanbooru._get_json("u")
    assert "u" not in mod.BaseDanbooru.REQUEST_CACHE


def test_connection_reset_propagates_without_retry(mod, session):
    """A TLS reset (Danbooru refusing the IP) surfaces as-is, and only once."""
    session.default = requests.exceptions.ConnectionError("Connection reset by peer")
    with pytest.raises(requests.exceptions.ConnectionError):
        mod.DanbooruPostTagsRetriever.execute(post_id="1")
    assert len(session.calls) == 1


#################################################################
# DanbooruPostTagsRetriever
#################################################################
def test_post_tags_split_by_category_and_full_excludes_meta(mod, session):
    session.routes["https://danbooru.donmai.us/posts/42.json"] = post(
        42, general="1girl blue_eyes", character="ray_(arknights)", copyright_="arknights",
        artist="someone", meta="highres absurdres", file_url="https://cdn/x.png",
    )
    full, general, character, copyright_, artist, meta, url = mod.DanbooruPostTagsRetriever.execute("42")
    assert general == "1girl, blue eyes"
    assert character == r"ray \(arknights\)"
    assert (copyright_, artist, meta) == ("arknights", "someone", "highres, absurdres")
    assert full == r"ray \(arknights\), arknights, someone, 1girl, blue eyes"
    assert url == "https://cdn/x.png"


def test_post_tags_image_url_falls_back_when_missing(mod, session):
    session.routes["https://danbooru.donmai.us/posts/7.json"] = post(7)
    assert mod.DanbooruPostTagsRetriever.execute("7")[-1] == "not_found"


#################################################################
# DanbooruRelatedTagsRetriever
#################################################################
def test_related_tags_filters_by_threshold_and_skips_deprecated(mod, session):
    session.routes[related_url("cat")] = {"related_tags": [
        related("cat", 1.0),
        related("animal_ears", 0.8),
        related("old_tag", 0.9, deprecated=True),
        related("rare", 0.1),
    ]}
    (out,) = mod.DanbooruRelatedTagsRetriever.execute("cat", threshold=0.3)
    assert out == "cat, animal ears"


def test_related_tags_n_min_falls_back_to_top_candidates(mod, session):
    session.routes[related_url("cat")] = {"related_tags": [
        related("cat", 1.0), related("a", 0.2), related("b", 0.1), related("c", 0.05),
    ]}
    (out,) = mod.DanbooruRelatedTagsRetriever.execute("cat", threshold=0.9, n_min_tags=3)
    assert out == "cat, a, b"


def test_related_tags_n_max_caps_the_result(mod, session):
    session.routes[related_url("cat")] = {"related_tags": [
        related("cat", 1.0), related("a", 0.9), related("b", 0.8), related("c", 0.7),
    ]}
    (out,) = mod.DanbooruRelatedTagsRetriever.execute("cat", n_max_tags=2)
    assert out == "cat, a"


def test_related_tags_strips_weights_and_dedupes_across_queries(mod, session):
    session.routes[related_url("cat")] = {"related_tags": [related("animal_ears", 0.9)]}
    session.routes[related_url("dog")] = {"related_tags": [related("animal_ears", 0.9), related("cat", 0.5)]}
    (out,) = mod.DanbooruRelatedTagsRetriever.execute("(cat:1.2) BREAK dog")
    assert out == "cat, animal ears, dog"


def test_related_tags_query_uses_category_order_and_danbooru_form(mod, session):
    url = related_url("ray_(arknights)", category="Character", order="Cosine")
    session.routes[url] = {"related_tags": [related("ray_(arknights)", cosine=1.0, frequency=0.0)]}
    (out,) = mod.DanbooruRelatedTagsRetriever.execute(
        r"ray \(arknights\)", category="Character", order="Cosine", threshold=0.5,
    )
    assert out == r"ray \(arknights\)"
    assert session.calls[0][0] == url


#################################################################
# DanbooruPopularPostsTagsRetriever
#################################################################
def page_of(start, count):
    return [post(i, general=f"tag{i}") for i in range(start, start + count)]


def test_popular_random_samples_n_from_n_pages_deterministically(mod, session):
    session.routes[popular_url(1)] = page_of(0, 20)
    session.routes[popular_url(2)] = page_of(20, 20)
    a = mod.DanbooruPopularPostsTagsRetriever.execute(n=2, random=True, seed=1)
    mod.BaseDanbooru.REQUEST_CACHE.clear()
    b = mod.DanbooruPopularPostsTagsRetriever.execute(n=2, random=True, seed=1)
    assert a == b
    assert len(a[0]) == 2 and all(isinstance(x, str) for x in a[0])
    assert [c[0] for c in session.calls[:2]] == [popular_url(1), popular_url(2)]


def test_popular_ordered_fetches_only_the_page_holding_the_rank(mod, session):
    session.routes[popular_url(2, date="2025-01-01", scale="week")] = page_of(20, 20)
    full, general, *_ = mod.DanbooruPopularPostsTagsRetriever.execute(
        date="2025-01-01", scale="week", n=2, random=False, offset=25,
    )
    assert general == ["tag25", "tag26"]
    assert [c[0] for c in session.calls] == [popular_url(2, date="2025-01-01", scale="week")]


def test_popular_ordered_spans_a_page_boundary(mod, session):
    session.routes[popular_url(1)] = page_of(0, 20)
    session.routes[popular_url(2)] = page_of(20, 20)
    _, general, *_ = mod.DanbooruPopularPostsTagsRetriever.execute(n=3, random=False, offset=19)
    assert general == ["tag19", "tag20", "tag21"]


def test_popular_ordered_raises_when_rank_does_not_exist(mod, session):
    session.routes[popular_url(1)] = page_of(0, 5)
    with pytest.raises(ValueError, match="only 5 popular posts"):
        mod.DanbooruPopularPostsTagsRetriever.execute(n=1, random=False, offset=7)


def test_popular_is_changed_ignores_seed_in_ordered_mode(mod):
    n = mod.DanbooruPopularPostsTagsRetriever
    assert n.IS_CHANGED("", "day", 1, False, 1, 3) == n.IS_CHANGED("", "day", 1, False, 2, 3)
    assert n.IS_CHANGED("", "day", 1, True, 1, 3) != n.IS_CHANGED("", "day", 1, True, 2, 3)


#################################################################
# DanbooruPostsDownloader
#################################################################
def search_url(tags, page):
    return f"https://danbooru.donmai.us/posts.json?tags={tags}&page={page}"


def test_downloader_writes_files_and_returns_output_relative_paths(mod, session, output_dir, fake_response):
    session.routes[search_url("cat", 1)] = [
        post(1, file_url="https://cdn/a.png"),
        post(2),  # no file_url: skipped, index not consumed
        post(3, file_url="https://cdn/b.jpg?x=1"),
    ]
    session.routes["https://cdn/a.png"] = fake_response(content=b"A")
    session.routes["https://cdn/b.jpg?x=1"] = fake_response(content=b"B")
    (paths,) = mod.DanbooruPostsDownloader.execute(tags="cat", n=3, dir_path="dl", prefix="cat")
    assert paths == ["dl/cat_1.png", "dl/cat_2.jpg"]
    assert (output_dir / "dl/cat_1.png").read_bytes() == b"A"
    assert (output_dir / "dl/cat_2.jpg").read_bytes() == b"B"


def test_downloader_continues_numbering_and_pages_by_twenty(mod, session, output_dir, fake_response):
    (output_dir / "more").mkdir()
    (output_dir / "more/4.png").write_bytes(b"old")
    session.routes[search_url("dog", 1)] = [post(i, file_url=f"https://cdn/{i}.png") for i in range(20)]
    session.routes[search_url("dog", 2)] = [post(i, file_url=f"https://cdn/{i}.png") for i in range(20, 40)]
    session.default = fake_response(content=b"x")
    (paths,) = mod.DanbooruPostsDownloader.execute(tags="dog", n=21, dir_path="more")
    assert paths[0] == "more/5.png" and paths[-1] == "more/25.png" and len(paths) == 21
    assert [c[0] for c in session.calls[:2]] == [search_url("dog", 1), search_url("dog", 2)]


def test_downloader_skips_a_failed_image_but_keeps_going(mod, session, output_dir, fake_response):
    session.routes[search_url("x", 1)] = [
        post(1, file_url="https://cdn/bad.png"),
        post(2, file_url="https://cdn/good.png"),
    ]
    session.routes["https://cdn/bad.png"] = fake_response(status_code=500)
    session.routes["https://cdn/good.png"] = fake_response(content=b"G")
    (paths,) = mod.DanbooruPostsDownloader.execute(tags="x", n=2, dir_path="f")
    assert paths == ["f/1.png"]
    assert (output_dir / "f/1.png").read_bytes() == b"G"


def test_downloader_does_not_refetch_an_existing_file(mod, session, output_dir, fake_response):
    session.routes[search_url("y", 1)] = [post(1, file_url="https://cdn/a.png")]
    session.routes["https://cdn/a.png"] = fake_response(content=b"new")
    (output_dir / "g").mkdir()
    (output_dir / "g/p_1.png").write_bytes(b"keep")
    (paths,) = mod.DanbooruPostsDownloader.execute(tags="y", n=1, dir_path="g", prefix="p")
    # The prefix scan counts p_1 and starts at p_2, so a new file is written, not p_1 overwritten.
    assert paths == ["g/p_2.png"]
    assert (output_dir / "g/p_1.png").read_bytes() == b"keep"
