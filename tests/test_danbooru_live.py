"""Each node against the real Danbooru API. Post 1 is Danbooru's first post."""

# https://danbooru.donmai.us/posts/1 -- kousaka_tamaki / to_heart_2, stable for years.
POST_ID = "1"


def test_post_tags_retriever(nodes):
    full, general, character, copyright_, artist, meta, image_url = nodes.DanbooruPostTagsRetriever.execute(POST_ID)
    assert "kousaka tamaki" in character
    assert "to heart 2" in copyright_
    assert general and artist
    assert full.startswith(character)
    # meta tags are excluded from full_tags
    assert not set(filter(None, meta.split(", "))) & set(full.split(", "))
    assert image_url.startswith("https://")


def test_related_tags_retriever(nodes):
    (out,) = nodes.DanbooruRelatedTagsRetriever.execute("cat ears", threshold=0.0, n_max_tags=5)
    tags = out.split(", ")
    assert tags[0] == "cat ears"
    assert 2 <= len(tags) <= 6
    assert "_" not in out


def test_related_tags_retriever_with_qualifier(nodes):
    (out,) = nodes.DanbooruRelatedTagsRetriever.execute(r"(kousaka tamaki:1.2)", category="Character", n_max_tags=3)
    assert out.split(", ")[0] == "kousaka tamaki"


def test_popular_posts_random(nodes):
    full, general, *_ = nodes.DanbooruPopularPostsTagsRetriever.execute(scale="day", n=2, random=True, seed=0)
    assert len(full) == 2 and len(general) == 2
    assert all(g for g in general)


def test_popular_posts_ordered_offset(nodes):
    a = nodes.DanbooruPopularPostsTagsRetriever.execute(scale="week", n=1, random=False, offset=0)
    b = nodes.DanbooruPopularPostsTagsRetriever.execute(scale="week", n=2, random=False, offset=0)
    assert a[0] == b[0][:1]  # rank 0 is the same whether n is 1 or 2
    assert b[0][0] != b[0][1]


def test_posts_downloader(nodes, output_dir):
    (paths,) = nodes.DanbooruPostsDownloader.execute(tags=f"id:{POST_ID}", n=1, dir_path="dl", prefix="p")
    assert paths == ["dl/p_1.jpg"] or (len(paths) == 1 and paths[0].startswith("dl/p_1."))
    assert (output_dir / paths[0]).stat().st_size > 0


def test_cache_serves_the_second_call_without_a_request(nodes, monkeypatch):
    url = f"https://danbooru.donmai.us/posts/{POST_ID}.json"
    nodes.BaseDanbooru._get_json(url)  # warm (or already warm from the first test)
    session = nodes._get_session()

    def boom(*a, **k):
        raise AssertionError("cache miss: a request went out")

    monkeypatch.setattr(session, "get", boom)
    assert nodes.BaseDanbooru._get_json(url)["id"] == int(POST_ID)
