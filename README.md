<div align="center">

<img src="assets/hordeplayer.png" width="128" height="128" alt="HordePlayer logo">

# HordePlayer

**A dependency-free, local-first video player for Linux — powered by ffmpeg.**

Play anything the browser can't. MKV, H.265, AC3/E-AC3 audio, HLS, and DASH —
converted on the fly by a tiny local server that speaks nothing but HTTP/1.1 and the
Python standard library.

[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-1e3a8a.svg)](LICENSE)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux%20x86__64-16a34a.svg)]()
[![Snap Store](https://img.shields.io/badge/snap-hordeplayer-82BFA1.svg?logo=snapcraft)](https://snapcraft.io/hordeplayer)
[![GitHub Release](https://img.shields.io/github/v/release/Hordekiller/HordePlayer)](https://github.com/Hordekiller/HordePlayer/releases)
[![CI](https://img.shields.io/github/actions/workflow/status/Hordekiller/HordePlayer/release.yml?branch=main)](https://github.com/Hordekiller/HordePlayer/actions)

[Install](#-installation) · [Usage](#-usage) · [CLI Reference](#-command-line-reference) ·
[Architecture](#-architecture) · [Build](#-building-from-source) · [License](#-license)

</div>

---

## Table of Contents

- [Highlights](#-highlights)
- [Why HordePlayer](#-why-hordeplayer)
- [Features](#-features)
- [Installation](#-installation)
- [Usage](#-usage)
- [Command Line Reference](#-command-line-reference)
- [Configuration](#-configuration)
- [Architecture](#-architecture)
- [Security & Privacy](#-security--privacy)
- [Building from Source](#-building-from-source)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)

---

## Highlights

- **Zero backend dependencies** — the server is pure Python 3 standard library. No Node, no
  nginx, no container, no daemon to fight with.
- **Codec-agnostic playback** — MKV, HEVC, AC3/E-AC3 (the ubiquitous Farsi-dubbed track format)
  that browsers refuse to play, remuxed/transcoded to MP4/AAC on demand.
- **Truly local** — binds `127.0.0.1` only. Your media never transits a third party.
- **One package type for every distro** — AppImage, `.deb`, `.rpm`, snap, or a per-user
  `install.sh` from the same codebase.
- **RTL / Persian-first UI** — designed for Persian-speaking users, usable by anyone.

---

## Why HordePlayer

Modern browsers can only decode a narrow slice of the media ocean. Persian film and TV
releases — like much of the world's archive — are overwhelmingly distributed as `.mkv` with
**AC3 or E-AC3 audio** (3+ channels) that no mainstream browser will touch. The classic
answer is "install VLC", but VLC has never been a good citizen for *linked* content, and its
UI is not what one wants to hand to a parent or a non-technical viewer.

HordePlayer sits between a browser's `<video>` element and the filesystem/network. A tiny
background server opportunistically asks `ffprobe` what a source actually contains, and only
when needed runs `ffmpeg` to produce a standard fragmented MP4 that any HTML5 player renders
natively — hardware acceleration included.

---

## Features

| Area | Capability |
|------|------------|
| **Sources** | Local files, direct HTTP(S) URLs, HLS (`.m3u8`), DASH (`.mpd`), drag & drop, file picker, persistent playlists |
| **Compatibility** | MP4, MKV, WebM, MOV, TS, AVI, FLV, WMV, HEVC, AV1 (browser-dependent) |
| **The killer feature** | Live remux/transcode of MKV + AC3/E-AC3 → MP4 + AAC via local ffmpeg ("Transcode" button) |
| **Audio** | Volume (0.5×–6× gain), dynamic normalization (`dynaudnorm`), EBU R128 loudness (`loudnorm`) |
| **Caching** | Background downloader with configurable retention (`prune`), enabling instant seeking on large files |
| **Player** | Custom overlay, buffer visualization, hover seek-preview, speeds 0.25×–3×, loop, subtitles, Picture-in-Picture, fullscreen, media-session integration |
| **UI** | 4-tab sidebar (Playlist / Audio / Settings / Help), 26 SVG symboicons, keyboard shortcuts, persistent preferences (localStorage), Persian RTL |

---

## Installation

### 1. Snap — every major distro

```bash
sudo snap install hordeplayer
```

Available on the [Snap Store](https://snapcraft.io/hordeplayer). Bundles ffmpeg; nothing else
to install.

### 2. AppImage — no install, rootless, portable

```bash
chmod +x HordePlayer-*-x86_64.AppImage
./HordePlayer-*-x86_64.AppImage
```

The AppImage self-extracts ffmpeg into `~/.cache/hordeplayer/` on first launch and reuses it,
so the player keeps working after the image is detached from memory and unmounted.

### 3. Debian / Ubuntu

```bash
sudo apt install ./hordeplayer_*_all.deb
hordeplayer
```

### 4. Fedora / RHEL

```bash
sudo dnf install ./hordeplayer-*.noarch.rpm
hordeplayer
```

### 5. From source — per-user, no root

```bash
./install.sh          # installs into ~/.local/bin, ~/.local/share, and your desktop
hordeplayer
```

---

## Usage

1. **Pick a source** — paste a link (HLS/DASH/MP4/MKV…) into the URL field and press
   **پخش / Play**, or drop a file directly onto the player.
2. **MKV or quiet AC3?** — press **تبدیل / Transcode** to route the source through ffmpeg
   (MP4/H.264/AAC, with your chosen audio pipeline).
3. **Tune it** — the **صدا / Audio** tab covers gain, normalization and loudness; the
   **پلیلیست** tab manages queues; the **تنظیمات / Settings** tab sets the server address,
   referer header, and seek step.
4. On first run a private server starts on `http://127.0.0.1:8787/` and the player opens in
   your default browser.

---

## Command Line Reference

| Command | Description |
|---------|-------------|
| `hordeplayer` | Start the server (if needed) and open the player |
| `hordeplayer --port 9000` | Use a custom port |
| `hordeplayer --stop` | Stop a running server |
| `hordeplayer --help` | Show usage |

Linked-list lifecycle note: the server is intentionally disowned from the terminal, so it
survives the calling shell; `--stop` cleans it up. A stale socket is freed automatically on
the next start.

---

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `HORDE_PORT` | `8787` | Default server port (also `--port`) |
| `HORDE_APP_DIR` | `<discovered>` | Explicit path to the app/base directory |
| `HORDE_CACHE` | `~/.cache/hordeplayer` | Override the cache location (respects `XDG_CACHE_HOME`) |
| `FFMPEG_BIN`, `FFPROBE_BIN` | auto-discovered | Explicit paths to `ffmpeg`/`ffprobe` |

Binary resolution order for the video tools: explicit env → AppImage bundle → next to the
app → `~/bin` → `PATH`.

Logs and PID live alongside the cache: `~/.cache/hordeplayer/{server.log,server.pid}`.

---

## Architecture

```
Browser ──(native <video>, HTTP)──►  HordePlayer server  (127.0.0.1:PORT)
                                        │  stdlib ThreadingHTTPServer
        ┌───────────────┬───────────────┼──────────────┬───────────────┐
   /health           /probe          /play         /proxy      /status
   liveness       ffprobe info    ffmpeg pipe    range-safe    progress
   /file/<id>      served cache                   forwarder
   /upload
```

The core is `app/server.py`, one dependency-free Python file:

- **`GET /health`** — liveness probe (used by the launcher's startup handshake).
- **`GET /probe`** — extracts stream metadata with `ffprobe` to decide remux-vs-encode.
- **`GET /play`** — streams a fragmented MP4 (`frag_keyframe+empty_moov`) produced by `ffmpeg`,
  either copied (`-c:v copy`) when the codec is already H.264 or transcoded
  (`libx264 -preset veryfast -crf 23`, AAC 160k, dual-mono layouts as needed).
- **`GET /proxy`** — forwards remote URLs while handling `Range` headers; sidesteps a known
  ffprobe crash when seeking through HTTP servers that mishandle ranged requests.
- **`GET /file/<id>`** — serves cached media; **`POST /upload`** ingests local files.
- **`GET /status`** — background cache-download progress (with pruning, keeping 5 items).

Transcoding rules for the audio pipeline: explicit `volume=` gain, `dynaudnorm`, or
`loudnorm=I=-16:TP=-1.5:LRA=11`, selected from the Audio tab. Video is keyframe-fragmented
MP4 with `default_base_moof`, so forward/reverse seeking works mid-stream via HTTP ranges.

---

## Security & Privacy

- Listens **only on the loopback interface** (`127.0.0.1` + `::1`); nothing is exposed to the
  LAN or WAN.
- No analytics, no telemetry, no remote code — the single outbound connection a source
  triggers is the one to the media host itself.
- Runs unprivileged; gated per-interface (seccomp/AppArmor) under strict snap confinement.
- **Troubleshooting note:** many Iranian media hosts to a fault still only answer *Iranian IPs*.
  If a source reports `unavailable`, **disable your VPN/proxy** and retry — the player shows
  the exact upstream failure code to make this obvious.

---

## Building from Source

```bash
# .deb, .rpm and AppImage → ./dist
bash packaging/build-all.sh

# individually
bash packaging/build-deb.sh
bash packaging/build-rpm.sh
bash packaging/build-appimage.sh

# snap (requires snapcraft + LXD, or use CI)
snapcraft pack            # → hordeplayer_1.0.0_amd64.snap
```

| Switch | Effect |
|--------|--------|
| `BUNDLE_FFMPEG=0` | Don't embed ffmpeg in the AppImage; use the system binary |
| `ARCH=arm64` | Cross-target the AppImage |

Every push on `main` runs a CI pipeline that produces all four package types and attaches
them to tag releases (`v*`).

---

## Project Structure

```
app/                 The complete application (server + static UI + web icons)
  server.py          Dependency-free HTTP/1.1 media server
  index.html         Persian/RTL player UI (SVG sprite, tabs, settings persistence)
assets/              Brand artwork and icon set (128/256/512/1024)
packaging/           Launcher, .desktop, spec/appstream metadata, build scripts
snap/                snapcraft.yaml for the Snap Store
scripts/             Dev wrappers (start.sh / stop.sh)
install.sh           Per-user installer    uninstall.sh   per-user removal
dist/                Built artifacts (gitignored)
.github/workflows/   CI: packages + snap, release on tags
```

---

## Development

Requirements: Python 3.8+, ffmpeg/ffprobe on `PATH` (or via `FFMPEG_BIN`), a browser.

```bash
git clone https://github.com/Hordekiller/HordePlayer.git
cd HordePlayer
python3 app/server.py 8787          # run the server in the foreground
# then open http://127.0.0.1:8787/
```

The UI is a single self-contained `index.html` — no build step, no framework, no JS bundle
to reconcile. Sanity-check a modified UI with `node --check` on an extracted inline script;
the server script round-trips through `python3 -m py_compile`.

---

## Contributing

Bug reports and feature ideas are welcome via the
[issue tracker](https://github.com/Hordekiller/HordePlayer/issues). Pull requests are
reviewed against the [GPL-3.0](LICENSE) license, no-codec-license-bundling requirement
(ffmpeg remains an external process), and a promise of simplicity: prefer the standard
library, one file, and no vendored blobs.

---

## License

[GPL-3.0-or-later](LICENSE) © 2026 Hordekiller

HordePlayer invokes `ffmpeg`/`ffprobe` strictly as **external processes**; no ffmpeg code is
linked into the player. ffmpeg is distributed under its own (L)GPL license and is bundled as
a separate artifact where included (AppImage, snap).