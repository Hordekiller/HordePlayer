<div align="center">

<img src="assets/hordeplayer.png" width="120" alt="HordePlayer">

# HordePlayer

**A professional local video player for Linux, powered by ffmpeg.**

Plays any link or local file in a clean web UI — including **MKV** and
**AC3/E-AC3** audio (common in Farsi-dubbed releases) that browsers can't play.

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)

</div>

---

## ✨ Features

- **Any source** — `mp4`, `mkv`, `webm`, `mov`, `ts`, HLS (`.m3u8`), DASH (`.mpd`), plus direct links.
- **MKV + AC3 to MP4/AAC** — a tiny local ffmpeg server remuxes/transcodes on the fly.
- **Audio boost & normalization** — simple gain (0.5×–6×), dynamic normalization, or EBU R128 `loudnorm`.
- **Background caching** — sources are downloaded in the background for fast seeking.
- **Professional UI** — tabs, SVG icons, playlist, playback speed, loop, subtitles, PiP, fullscreen, drag & drop, and rich keyboard shortcuts.
- **RTL / Persian-first** interface.
- **Private by design** — everything runs locally on `127.0.0.1`; nothing leaves your machine (except fetching the video itself).
- **Portable** — ships as AppImage, `.deb`, `.rpm`, or a single `install.sh`.

## 📋 Requirements

- **Linux** (x86_64)
- **Python 3.8+** (uses only the standard library)
- **ffmpeg** — required only for MKV/AC3 transcoding and audio boost.
  The AppImage bundles a static ffmpeg, so no system install is needed there.

## 📦 Install

### AppImage (portable, no root)
```bash
chmod +x HordePlayer-*-x86_64.AppImage
./HordePlayer-*-x86_64.AppImage
```

### Debian / Ubuntu
```bash
sudo apt install ./hordeplayer_*_all.deb
hordeplayer
```

### Fedora / RHEL
```bash
sudo dnf install ./hordeplayer-*.noarch.rpm
hordeplayer
```

### From source (per-user, no root)
```bash
./install.sh          # installs into ~/.local
hordeplayer
```

## 🚀 Usage

1. Paste a video link (or drop a file onto the player) and click **پخش / Play**.
2. For MKV files or quiet AC3 audio, click **تبدیل / Transcode** to route through ffmpeg.
3. Tune audio in the **صدا / Audio** tab, playlist in **پلی‌لیست**, server/referer in **تنظیمات / Settings**.

### Command line
```bash
hordeplayer                # start server + open the player
hordeplayer --port 9000    # custom port
hordeplayer --stop         # stop the running server
```

### Keyboard shortcuts
| Key | Action | Key | Action |
|-----|--------|-----|--------|
| `Space` / `K` | Play / pause | `M` | Mute |
| `←` / `→` | Seek | `F` | Fullscreen |
| `↑` / `↓` | Volume | `L` | Loop |
| `,` / `.` | Speed | `?` | Help |

## 🛠 Building packages

```bash
bash packaging/build-all.sh      # builds .deb, .rpm and AppImage into ./dist
```
Individual builders: `packaging/build-deb.sh`, `build-rpm.sh`, `build-appimage.sh`.

- `BUNDLE_FFMPEG=0` — don't embed ffmpeg in the AppImage (use the system one).
- `ARCH=arm64` — build the AppImage for another architecture.

## ⚙️ How it works

`app/server.py` is a dependency-free Python HTTP server that:

- serves the player UI (`index.html`) and assets,
- `GET /probe` reads media info with `ffprobe`,
- `GET /play` pipes a fragmented MP4 stream produced by `ffmpeg`,
- `GET /proxy` forwards remote URLs (avoids a known ffprobe seek crash),
- `GET /status` reports background-download progress.

The cache and logs live in `${XDG_CACHE_HOME:-~/.cache}/hordeplayer`.

## 🩺 Troubleshooting

- **"Source unavailable"** — many Iranian hosts only allow IRAN IPs; **turn off your VPN**.
- **MKV won't play directly** — expected; use the **Transcode** button (needs ffmpeg).
- **Logo/UI icons missing** — make sure the server is running (they're served locally).

## 📄 License

[GPL-3.0-or-later](LICENSE) © 2026 Hordekiller

ffmpeg is a separate program distributed under its own (L)GPL license and is
invoked as an external process; it is not linked into HordePlayer.
