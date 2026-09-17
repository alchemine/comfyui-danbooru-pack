# ComfyUI-Danbooru-Pack

[English](README.md) | [한국어](README_ko.md)

Retrieves tags from Danbooru posts and downloads Danbooru images.

## Usage

Give **Danbooru Post Tags Retriever** a post id and read the tags back split by category, with the image URL. **Danbooru Related Tags Retriever** takes a tag and returns the tags Danbooru relates to it. **Danbooru Popular Posts Tags Retriever** returns the tags of the day's, week's or month's popular posts, either a random sample or one rank at a time. **Danbooru Posts Downloader** saves the images of a tag search into the output folder.

> [!NOTE]
> Responses are cached to limit requests: a single post (by id) for the process lifetime, the volatile endpoints (popular / related / search) for 1 hour. Heavy use can still hit Danbooru's rate limits.

### Webshare proxy (optional)

Set `WEBSHARE_PROXY_USERNAME` / `WEBSHARE_PROXY_PASSWORD` in `.env` (see `.env.example`) to route the Danbooru nodes through a proxy; leave them unset to connect directly.

## Example

[`workflows/comfyui-danbooru-pack-workflow.json`](workflows/comfyui-danbooru-pack-workflow.json)

![Workflow](workflows/comfyui-danbooru-pack-workflow.png)

## Installation

Search for **ComfyUI-Danbooru-Pack** in ComfyUI Manager, or:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/alchemine/comfyui-danbooru-pack
pip install -r comfyui-danbooru-pack/requirements.txt
```

## Nodes (`DanbooruPack/Danbooru`)

### Danbooru Post Tags Retriever

| Parameter | Type | Description |
|-----------|------|-------------|
| `post_id` | STRING | Danbooru post ID |

| Output | Description |
|--------|-------------|
| `full_tags` | All tags (character + copyright + artist + general, excludes meta) |
| `general_tags` | General tags only |
| `character_tags` | Character tags only |
| `copyright_tags` | Copyright tags only |
| `artist_tags` | Artist tags only |
| `meta_tags` | Meta tags only |
| `image_url` | Image URL |

### Danbooru Related Tags Retriever

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | STRING | (required) | Input tag(s) |
| `category` | ENUM | "General" | Tag category filter (General/Character/Copyright/Artist/Meta) |
| `order` | ENUM | "Frequency" | Sort order (Cosine/Jaccard/Overlap/Frequency) |
| `threshold` | FLOAT | 0.3 | Minimum similarity threshold |
| `n_min_tags` | INT | 0 | Minimum number of tags to return |
| `n_max_tags` | INT | 100 | Maximum number of tags to return |

### Danbooru Popular Posts Tags Retriever

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | STRING | "" | Date (YYYY-MM-DD format, empty for latest) |
| `scale` | ENUM | "day" | Time scale (day/week/month) |
| `n` | INT | 1 | Number of posts to retrieve |
| `random` | BOOLEAN | True | `True`: random sample of `n` posts; `False`: the ranked posts at `[offset, offset+n)` in popularity order |
| `seed` | INT | 0 | Random seed (only used when `random=True`) |
| `offset` | INT | 0 | Starting rank in popularity order (only used when `random=False`). Has `control_after_generate` — set it to *increment* to step down the ranking one post per run. Raises if the rank doesn't exist. |

Outputs are **lists** (one entry per post): `full_tags` / `general_tags` / `character_tags` / `copyright_tags` / `artist_tags` / `meta_tags`.

> [!TIP]
> To walk the ranking one at a time, set `random=False`, `n=1`, and `offset`'s control to *increment*. Each queue returns the next most-popular post, fetching only the single page it lives on.

### Danbooru Posts Downloader

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tags` | STRING | "" | Search tags |
| `n` | INT | 1 | Number of images to download |
| `dir_path` | STRING | "" | Output directory (relative to ComfyUI output folder) |
| `prefix` | STRING | "" | Filename prefix |

## Configuration

### Connection host

The TLS connection is opened to `safebooru.donmai.us`, which shares Danbooru's certificate, with the `Host` header on `danbooru.donmai.us`, so the responses are Danbooru's own. Some networks reset every TLS handshake naming `danbooru.donmai.us`; this way the nodes work there too. Image downloads from `cdn.donmai.us` are unaffected.

## License

GPL-3.0 — see [LICENSE](LICENSE).
