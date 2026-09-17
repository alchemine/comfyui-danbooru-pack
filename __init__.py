"""Custom nodes mappings."""

from .nodes.danbooru_requests import (
    DanbooruRelatedTagsRetriever,
    DanbooruPostTagsRetriever,
    DanbooruPopularPostsTagsRetriever,
    DanbooruPostsDownloader,
)


NODE_CLASS_MAPPINGS = {
    # DanbooruPack/Danbooru ##########################################################
    "DanbooruRelatedTagsRetriever": DanbooruRelatedTagsRetriever,
    "DanbooruPostTagsRetriever": DanbooruPostTagsRetriever,
    "DanbooruPopularPostsTagsRetriever": DanbooruPopularPostsTagsRetriever,
    "DanbooruPostsDownloader": DanbooruPostsDownloader,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    # DanbooruPack/Danbooru ##########################################################
    "DanbooruRelatedTagsRetriever": "Danbooru Related Tags Retriever",
    "DanbooruPostTagsRetriever": "Danbooru Post Tags Retriever",
    "DanbooruPopularPostsTagsRetriever": "Danbooru Popular Posts Tags Retriever",
    "DanbooruPostsDownloader": "Danbooru Posts Downloader",
}
