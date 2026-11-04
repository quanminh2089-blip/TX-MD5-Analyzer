# MinhQuan v0.7 — Android UI prototype

This version contains only presentation and **offline demo** login flows. No Tài/Xỉu/MD5 predictor, OCR, screen capture, overlays, real backend authentication, network port scanning or server connection.

## Changes
- Splash: small black-background loading card with spinning green mask avatar, 3 seconds.
- Free demo key: `FreeKey_MinhQuan`; key dialog retains increasing counter -1s, -2s, ...
- Account page: removed the subtitle and welcome line, added Admin / Zalo / Telegram contact details.
- Offline demo login: The username and password specified by the owner are checked locally. Only a SHA-256 digest is embedded, not the plaintext password. This is **not secure real-user authentication**; any shipped local credential can be extracted/bypassed. Never use real secrets here.
- Login success opens an animated hacker-style **local visual simulation**: Matrix falling characters and simulated virtual-port success messages (no actual network connections).
- Key accepted notification: `ĐĂNG NHẬP APP THÀNH CÔNG✅` with a compact custom Android notification featuring the app avatar to the left of the message (exact appearance controlled by Android/OEM and notification settings).

## Build with GitHub Actions
Upload the contents (not an extra enclosing folder) into the existing repository on main. The provided `.github/workflows/android-build.yml` builds a debug APK and uploads `MinhQuan-debug` as an artifact.

## Important
The ZIP is **source code**, not a built or device-tested APK. The custom notification may be rendered differently by different Android versions and skins. Notification permission must be granted on Android 13+ to display it.
