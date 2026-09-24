"""Embed the project page and its media into one offline HTML, then zip it."""

import base64
import json
import mimetypes
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import zipfile


ROOT = Path(__file__).resolve().parent


def build():
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    javascript = (ROOT / "main.js").read_text(encoding="utf-8")
    page, count = re.subn(r'<link\b[^>]*href="(?:\./)?styles\.css"[^>]*>',
                         lambda _: f"<style>\n{css}\n</style>", page)
    if count != 1:
        raise ValueError("Expected exactly one styles.css link")
    page, count = re.subn(r'<script\b[^>]*src="(?:\./)?main\.js"[^>]*></script>', "", page)
    if count != 1:
        raise ValueError("Expected exactly one main.js script")

    assets = {}
    paths = {}

    def embed(match):
        attribute, url = match.groups()
        if url.startswith("#") or urlsplit(url).scheme or url.startswith("//"):
            return match.group(0)
        path = (ROOT / unquote(urlsplit(url).path)).resolve()
        # The fallback download points to the same compatible summary video.
        if path == ROOT.parent / "video_PAF.mp4":
            path = ROOT / "media/video_PAF_h264.mp4"
        if not path.is_file():
            raise FileNotFoundError(f"Missing page asset: {url}")
        if path not in paths:
            key = f"asset-{len(paths)}"
            paths[path] = key
            assets[key] = {
                "type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                "data": base64.b64encode(path.read_bytes()).decode("ascii"),
            }
        return f'data-bundle-{attribute}="{paths[path]}"'

    # Only rewrite URL attributes in markup, not strings inside CSS or scripts.
    page = re.sub(r'<[^>]+>', lambda tag: re.sub(
        r'\b(src|href|poster)="([^"]+)"', embed, tag.group(0)), page)

    loader = r"""
(() => {
  const payload = document.getElementById('embedded-assets');
  const assets = JSON.parse(payload.textContent);
  const urls = new Map();
  for (const [key, asset] of Object.entries(assets)) {
    const chunks = [];
    // Chunked decoding avoids oversized function calls for long videos.
    for (let offset = 0; offset < asset.data.length; offset += 262144) {
      const binary = atob(asset.data.slice(offset, offset + 262144));
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      chunks.push(bytes);
    }
    urls.set(key, URL.createObjectURL(new Blob(chunks, { type: asset.type })));
    delete assets[key];
  }
  for (const attribute of ['src', 'href', 'poster']) {
    document.querySelectorAll(`[data-bundle-${attribute}]`).forEach(element => {
      const key = element.getAttribute(`data-bundle-${attribute}`);
      element.setAttribute(attribute, urls.get(key));
      element.removeAttribute(`data-bundle-${attribute}`);
    });
  }
  payload.remove();
})();
"""
    safe_js = (loader + "\n" + javascript).replace("</script", "<\\/script")
    embedded = ('<script id="embedded-assets" type="application/json">'
                + json.dumps(assets, separators=(",", ":"))
                + '</script>\n<script>\n' + safe_js + '\n</script>\n')
    page = page.replace("</body>", embedded + "</body>")
    output = ROOT / "PAF-standalone.html"
    output.write_text(page, encoding="utf-8")
    archive = ROOT / "PAF-standalone.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as bundle:
        bundle.write(output, arcname=output.name)
    print(f"Embedded {len(assets)} unique assets")
    for path in (output, archive):
        print(f"{path.name}: {path.stat().st_size / 1024**2:.1f} MiB")


if __name__ == "__main__":
    build()
