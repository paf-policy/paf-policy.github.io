"""Local static preview with byte ranges for native video seeking."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re


class VideoPreviewHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        self.range_remaining = None
        path = Path(self.translate_path(self.path))
        requested = self.headers.get("Range")
        # Use the standard handler for directories, ordinary requests and If-Range.
        if not requested or not path.is_file() or self.headers.get("If-Range"):
            return super().send_head()
        try:
            source = path.open("rb")
        except OSError:
            self.send_error(404, "File not found")
            return None
        size = path.stat().st_size
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", requested.strip())
        # Multipart ranges are optional; serve the complete file for unsupported syntax.
        if not match or not any(match.groups()):
            source.close()
            return super().send_head()
        first, last = match.groups()
        if first:
            start = int(first)
            end = min(int(last), size - 1) if last else size - 1
        else:
            start = max(0, size - int(last))
            end = size - 1
        if start >= size or end < start:
            source.close()
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        self.range_remaining = end - start + 1
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(str(path)))
        self.send_header("Content-Length", str(self.range_remaining))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Last-Modified", self.date_time_string(path.stat().st_mtime))
        self.end_headers()
        source.seek(start)
        return source

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def copyfile(self, source, output):
        try:
            if self.range_remaining is None:
                return super().copyfile(source, output)
            remaining = self.range_remaining
            while remaining:
                chunk = source.read(min(256 * 1024, remaining))
                if not chunk:
                    break
                output.write(chunk)
                remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass  # Browsers cancel in-flight requests when seeking or pausing.


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    handler = partial(VideoPreviewHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Preview: http://localhost:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
