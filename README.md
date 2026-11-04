# MinhQuan v0.6 — Android UI prototype

This source tree replaces the previous TX-MD5 Analyzer feature prototype. It now contains **only the MinhQuan UI flow**, with no screen capture, OCR, game history reader, prediction, overlays, or background service.

## Flow

1. Launch app: solid black screen + a compact 174 x 100 dp loading card with a circular rotating green-mask avatar, for three seconds. No logo/text behind the loading card. The loading caption is visual only (no server request).
2. The centered **MinhQuan'z** key dialog appears. The displayed timer counts elapsed seconds (`-1s`, `-2s`, etc.). `Get Key` fills the local demo key `FreeKey_MinhQuan`; `OK` validates the key locally.
3. After a correct key, MinhQuan requests notification permission on Android 13+ if needed and sends **ĐĂNG NHẬP APP THÀNH CÔNG✅** when permitted. If notifications are blocked by the user or device, it cannot send them.
4. The screen below the dialog is the new member login UI: green-mask avatar at the top and styled username/password fields in a central card. This is **UI only**. The login button shows a placeholder message; no accounts, remote validation, or password transmission/storage have been implemented.

## Upgrade the existing GitHub repo from Termux

After downloading this ZIP into `~/storage/downloads`:

```bash
cd ~/TX-MD5-Analyzer/TX-MD5-Analyzer
git pull --ff-only origin main
rm -f app/src/main/java/com/txanalyzer/CaptureService.java app/src/main/java/com/txanalyzer/HistoryReader.java
unzip -o ~/storage/downloads/MinhQuan-Android-v0.6-source.zip -d .
git add -A
git commit -m "MinhQuan v0.6 new login UI and notification"
git push origin main
```

The repository's GitHub Actions workflow builds an Android debug APK and publishes artifact `MinhQuan-debug` when successful. Installations can update older apps because the application ID stays `com.txanalyzer` (a different signing key may prevent an in-place install).

## Notes

- Notification permission is explicitly requested after accepting the key. A successful local key entry does not imply real server login.
- There is no prediction or gambling-related function.
- This ZIP is source code, not a prebuilt APK. Building/testing the app on an Android device is still required.
