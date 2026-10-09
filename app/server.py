#!/usr/bin/env python3
"""
Local media server for HordePlayer.

Why it exists:
  Browsers cannot play the .mkv container, and cannot decode AC3/E-AC3 audio
  (common in Farsi-dubbed files). This server remuxes/transcodes any source on
  the fly with ffmpeg into a browser-friendly fragmented MP4 stream, and can
  amplify / normalize the audio.

Run:  python3 server.py            (default http://localhost:8787)
      python3 server.py 9000       (custom port)
"""

import hashlib
import json
import mimetypes
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "hordeplayer"


def _user_cache_dir():
    """User-writable cache dir (works for system installs too)."""
    if os.environ.get("HORDE_CACHE"):
        return os.environ["HORDE_CACHE"]
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(
        os.path.expanduser("~"), ".cache")
    d = os.path.join(base, APP_NAME)
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        d = os.path.join("/tmp", APP_NAME + "-" + str(os.getuid()))
        os.makedirs(d, exist_ok=True)
    return d


CACHE = _user_cache_dir()
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def find_binary(name):
    """Locate ffmpeg/ffprobe: env override, bundled (AppImage), then system."""
    appdir = os.environ.get("APPDIR", "")
    candidates = [
        os.environ.get(name.upper() + "_BIN"),
        os.environ.get("HORDE_" + name.upper()),
        os.path.join(appdir, "usr", "bin", name) if appdir else None,
        os.path.join(HERE, "bin", name),
        os.path.join(os.path.dirname(HERE), "bin", name),
        os.path.join(os.path.expanduser("~"), "bin", name),
        shutil.which(name),
    ]
    for cand in candidates:
        if cand and os.path.exists(cand):
            return cand
    return name


FFMPEG = find_binary("ffmpeg")
FFPROBE = find_binary("ffprobe")

SERVER_PORT = 8787
LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1", "[::1]")

_RANGE_RE = re.compile(r"bytes=(\d+)-(\d*)")

# background download cache: url-hash -> job dict
CACHE_JOBS = {}
CACHE_LOCK = threading.Lock()


def cache_key(url):
    return hashlib.sha1(url.encode("utf-8", "ignore")).hexdigest()


def cache_status(url):
    job = CACHE_JOBS.get(cache_key(url))
    if not job:
        return {"state": "none"}
    return {"state": job["state"], "downloaded": job.get("downloaded", 0),
            "total": job.get("total", 0)}


def prune_cache(keep=5):
    """Keep cache bounded: drop leftover .part files and the oldest media"""
    medias = []
    try:
        for name in os.listdir(CACHE):
            p = os.path.join(CACHE, name)
            if name.endswith(".part"):
                if time.time() - os.path.getmtime(p) > 3600:
                    try:
                        os.remove(p)
                    except OSError:
                        pass
            elif name.endswith(".media"):
                medias.append((os.path.getmtime(p), p))
    except OSError:
        return
    medias.sort(reverse=True)
    for _, p in medias[keep:]:
        try:
            os.remove(p)
        except OSError:
            pass


def start_cache(url, referer):
    """Download the whole remote file to disk in the background (once per url)."""
    key = cache_key(url)
    with CACHE_LOCK:
        job = CACHE_JOBS.get(key)
        if job and job["state"] in ("downloading", "ready"):
            return job
        # no job, or a previous attempt errored -> (re)start fresh
        job = {"state": "downloading", "downloaded": 0, "total": 0,
               "path": os.path.join(CACHE, key + ".media"), "error": None}
        CACHE_JOBS[key] = job
    prune_cache()
    threading.Thread(target=_download, args=(key, url, referer), daemon=True).start()
    return job


def _download(key, url, referer):
    job = CACHE_JOBS[key]
    tmp = job["path"] + ".part"
    headers = {"User-Agent": UA, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    try:
        up = urllib.request.urlopen(
            urllib.request.Request(url, headers=headers), timeout=60)
        total = int(up.headers.get("Content-Length", 0) or 0)
        job["total"] = total
        got = 0
        with open(tmp, "wb") as f:
            while True:
                chunk = up.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                job["downloaded"] = got
        up.close()
        os.replace(tmp, job["path"])
        job["state"] = "ready"
    except Exception as e:
        job["state"] = "error"
        job["error"] = str(e)
        try:
            os.remove(tmp)
        except OSError:
            pass


def source_for(url, referer):
    """Pick the best ffmpeg input for a remote URL.

    - if fully cached on disk -> use the local file (fast, seekable)
    - otherwise start a background download and read live through our proxy
      (avoids the ffmpeg HTTP-seek segfault and mkv/AC3 issues)
    """
    if not url.lower().startswith(("http://", "https://")):
        return url
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    if host in LOCAL_HOSTS:
        return url
    job = CACHE_JOBS.get(cache_key(url))
    if job and job["state"] == "ready":
        return job["path"]
    start_cache(url, referer)
    return proxied(url, referer)


def proxied(url, referer):
    """Route remote http(s) URLs through our own /proxy endpoint.

    The static ffmpeg build segfaults when it does HTTP range-seeking against
    some nginx hosts (e.g. the TCI iptv box). Reading through our proxy, which
    we fully control, avoids that crash and keeps seeking working.
    """
    if not url.lower().startswith(("http://", "https://")):
        return url
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    if host in LOCAL_HOSTS:
        return url
    q = urllib.parse.urlencode({"url": url, "referer": referer or ""})
    return "http://127.0.0.1:%d/proxy?%s" % (SERVER_PORT, q)


def json_response(handler, obj, status=200):
    data = json.dumps(obj).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(data)


def build_input_args(url, referer):
    """HTTP-only input options (ffmpeg rejects -user_agent/-headers for local files)."""
    args = []
    if url.lower().startswith(("http://", "https://")):
        args += ["-user_agent", UA]
        if referer:
            args += ["-headers", "Referer: %s\r\n" % referer]
    return args


def probe(url, referer):
    eff = source_for(url, referer)
    cmd = [FFPROBE, "-v", "quiet", "-print_format", "json",
           "-show_format", "-show_streams"]
    cmd += build_input_args(eff, referer)
    cmd += [eff]
    out = subprocess.check_output(cmd, timeout=60)
    info = json.loads(out)
    duration = 0.0
    try:
        duration = float(info.get("format", {}).get("duration", 0) or 0)
    except (TypeError, ValueError):
        pass
    vcodec = None
    acodec = None
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and vcodec is None:
            vcodec = s.get("codec_name")
        if s.get("codec_type") == "audio" and acodec is None:
            acodec = s.get("codec_name")
    return {"duration": duration, "vcodec": vcodec, "acodec": acodec}


def audio_filter(amode, gain):
    parts = []
    try:
        gain = float(gain)
    except (TypeError, ValueError):
        gain = 1.0
    gain = max(0.1, min(16.0, gain))
    if amode == "loudnorm":
        parts.append("loudnorm=I=-16:TP=-1.5:LRA=11")
    elif amode == "dynaudnorm":
        if abs(gain - 1.0) > 0.001:
            parts.append("volume=%s" % gain)
        parts.append("dynaudnorm=f=150:g=15")
    else:  # gain / off
        if abs(gain - 1.0) > 0.001:
            parts.append("volume=%s" % gain)
    return ",".join(parts)


def build_ffmpeg(url, start, vcodec, amode, gain, referer):
    eff = source_for(url, referer)
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error"]
    cmd += build_input_args(eff, referer)
    if start and start > 0:
        cmd += ["-ss", str(start)]
    cmd += ["-i", eff]
    cmd += ["-map", "0:v:0?", "-map", "0:a:0?", "-sn", "-dn"]
    if (vcodec or "").lower() in ("h264", "avc1"):
        cmd += ["-c:v", "copy"]
    else:
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-g", "48"]
    cmd += ["-c:a", "aac", "-b:a", "160k", "-ac", "2"]
    af = audio_filter(amode, gain)
    if af:
        cmd += ["-af", af]
    cmd += ["-movflags", "frag_keyframe+empty_moov+default_base_moof",
            "-f", "mp4", "pipe:1"]
    return cmd


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "HordePlayer/1.0"
    sys_version = ""

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    # ---------- POST (upload local files) ----------
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/upload":
            return json_response(self, {"error": "not found"}, 404)
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        fid = uuid.uuid4().hex
        path = os.path.join(CACHE, fid)
        remaining = length
        with open(path, "wb") as f:
            while remaining > 0:
                chunk = self.rfile.read(min(1 << 20, remaining))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
        self.log_message("uploaded %d bytes -> %s", length, fid)
        return json_response(self, {"id": fid, "bytes": length})

    # ---------- GET ----------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/health":
            return json_response(self, {"ok": True, "ffmpeg": os.path.exists(FFMPEG)})

        if path == "/status":
            url = (qs.get("url") or [""])[0]
            return json_response(self, cache_status(url))

        if path == "/proxy":
            return self.handle_proxy(qs)

        if path.startswith("/file/"):
            return self.serve_file(path[len("/file/"):])

        if path == "/probe":
            url = (qs.get("url") or [""])[0]
            referer = (qs.get("referer") or [""])[0]
            if not url:
                return json_response(self, {"error": "missing url"}, 400)
            try:
                info = probe(url, referer)
                info["cache"] = cache_status(url)
                return json_response(self, info)
            except subprocess.TimeoutExpired:
                return json_response(self, {"error": "probe timeout"}, 504)
            except Exception as e:
                return json_response(self, {"error": str(e)}, 500)

        if path == "/play":
            return self.handle_play(qs)

        return self.serve_static(path)

    def handle_proxy(self, qs):
        target = (qs.get("url") or [""])[0]
        if not target:
            return json_response(self, {"error": "missing url"}, 400)
        referer = (qs.get("referer") or [""])[0]
        headers = {"User-Agent": UA, "Accept": "*/*", "Connection": "close"}
        if referer:
            headers["Referer"] = referer
        rng = self.headers.get("Range")
        if rng:
            headers["Range"] = rng
        try:
            up = urllib.request.urlopen(
                urllib.request.Request(target, headers=headers), timeout=60)
        except urllib.error.HTTPError as e:
            up = e
        except Exception as e:
            return json_response(self, {"error": "proxy: %s" % e}, 502)

        status = getattr(up, "status", 200) or 200
        self.send_response(status)
        self.send_header("Content-Type", up.headers.get("Content-Type", "application/octet-stream"))
        self.send_header("Accept-Ranges", up.headers.get("Accept-Ranges", "bytes"))
        cr = up.headers.get("Content-Range")
        if cr:
            self.send_header("Content-Range", cr)
        cl = up.headers.get("Content-Length")
        if cl:
            self.send_header("Content-Length", cl)
        else:
            self.send_header("Transfer-Encoding", "chunked")
        self._cors()
        self.end_headers()
        try:
            while True:
                chunk = up.read(1 << 16)
                if not chunk:
                    break
                if cl:
                    self.wfile.write(chunk)
                else:
                    self.wfile.write(b"%X\r\n" % len(chunk))
                    self.wfile.write(chunk)
                    self.wfile.write(b"\r\n")
            if not cl:
                self.wfile.write(b"0\r\n\r\n")
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            try:
                up.close()
            except Exception:
                pass

    def serve_file(self, fid):
        fid = os.path.basename(fid)
        path = os.path.join(CACHE, fid)
        if not os.path.isfile(path):
            self.send_response(404)
            self._cors()
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        size = os.path.getsize(path)
        rng = self.headers.get("Range")
        m = _RANGE_RE.match(rng) if rng else None
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else size - 1
            end = min(end, size - 1)
            length = max(0, end - start + 1)
            self.send_response(206)
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
        else:
            start, length = 0, size
            self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        self._cors()
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                d = f.read(min(1 << 20, remaining))
                if not d:
                    break
                try:
                    self.wfile.write(d)
                except (BrokenPipeError, ConnectionResetError):
                    return
                remaining -= len(d)

    def handle_play(self, qs):
        url = (qs.get("url") or [""])[0]
        if not url:
            return json_response(self, {"error": "missing url"}, 400)
        referer = (qs.get("referer") or [""])[0]
        vcodec = (qs.get("vcodec") or [""])[0]
        amode = (qs.get("amode") or ["off"])[0]
        gain = (qs.get("gain") or ["1"])[0]
        try:
            start = float((qs.get("start") or ["0"])[0])
        except ValueError:
            start = 0.0

        cmd = build_ffmpeg(url, start, vcodec, amode, gain, referer)
        self.log_message("play start=%.1fs amode=%s gain=%s vcodec=%s", start, amode, gain, vcodec)
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            return json_response(self, {"error": "ffmpeg launch failed: %s" % e}, 500)

        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Transfer-Encoding", "chunked")
        self._cors()
        self.end_headers()

        try:
            while True:
                chunk = proc.stdout.read(65536)
                if not chunk:
                    break
                self.wfile.write(b"%X\r\n" % len(chunk))
                self.wfile.write(chunk)
                self.wfile.write(b"\r\n")
            self.wfile.write(b"0\r\n\r\n")
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            proc.kill()
            try:
                err = proc.stderr.read(4000)
                if err:
                    sys.stderr.write(err.decode("utf-8", "ignore"))
            except Exception:
                pass
            try:
                proc.stdout.close()
                proc.stderr.close()
            except Exception:
                pass

    def serve_static(self, path):
        if path in ("/", ""):
            path = "/index.html"
        safe = os.path.normpath(path).lstrip("/")
        full = os.path.join(HERE, safe)
        if not full.startswith(HERE) or not os.path.isfile(full):
            self.send_response(404)
            self._cors()
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript",
                                                  "application/json",
                                                  "image/svg+xml"):
            ctype += "; charset=utf-8"
        with open(full, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)


class V6Server(ThreadingHTTPServer):
    address_family = socket.AF_INET6
    daemon_threads = True


def main():
    global SERVER_PORT
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    SERVER_PORT = port
    if not os.path.exists(FFMPEG):
        print("WARNING: ffmpeg not found (looked for %s). Transcoding will fail." % FFMPEG)
    print("HordePlayer server:    http://127.0.0.1:%d" % port)
    print("Open the player at:    http://127.0.0.1:%d/" % port)
    print("ffmpeg:                %s" % FFMPEG)
    print("cache:                 %s" % CACHE)

    # also listen on IPv6 ::1 so "localhost" works whichever family the browser picks
    try:
        srv6 = V6Server(("::1", port), Handler)
        threading.Thread(target=srv6.serve_forever, daemon=True).start()
        print("IPv6 listener:         http://[::1]:%d/" % port)
    except OSError as e:
        print("(IPv6 listener unavailable: %s)" % e)

    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    srv.daemon_threads = True
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
