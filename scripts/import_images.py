"""Download only user-reviewed, openly licensed images into static/images.

Usage: python scripts/import_images.py images.json
Each JSON item: {"url": "https://...", "filename": "rice.jpg", "license": "CC BY 4.0", "attribution": "..."}.
Keep the resulting images.json and ATTRIBUTION.md with the deployment.
"""
import json, mimetypes, sys
from pathlib import Path
from urllib.request import Request, urlopen

dest = Path(__file__).parents[1] / "app/static/images"
dest.mkdir(exist_ok=True)
items = json.loads(Path(sys.argv[1]).read_text())
credits = []
for item in items:
    if not item.get("license", "").lower().startswith(("cc", "public domain")):
        raise ValueError(f"Not an approved open licence: {item['filename']}")
    name = Path(item["filename"]).name
    response = urlopen(Request(item["url"], headers={"User-Agent": "AmarDokan-image-import/1.0"}), timeout=20)
    content_type = response.headers.get_content_type()
    if not content_type.startswith("image/") or response.length and response.length > 8_000_000:
        raise ValueError(f"Unsafe image response for {name}")
    (dest / name).write_bytes(response.read(8_000_001))
    if (dest / name).stat().st_size > 8_000_000: (dest / name).unlink(); raise ValueError(f"Image too large: {name}")
    credits.append(f"- {name}: {item['license']} — {item.get('attribution','attribution required')} — {item['url']}")
(dest / "ATTRIBUTION.md").write_text("# Image credits\n\n" + "\n".join(credits) + "\n")
