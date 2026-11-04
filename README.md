# MinhQuan MAGICOS WebView v1.4

- Preserves the original rotating avatar intro and `MinhQuan'z` key dialog from v1.3, including `FreeKey_MinhQuan` and Get Key.
- After correct key, opens the MAGICOS UI extracted from `magicos.py` inside an Android WebView. No game launch, overlay or accessibility permissions.
- `app/src/main/assets/index.html` is the concatenation of the original MAGICOS HTML/CSS/JS source, not a redesigned mockup. `phone-app.html` is also included.
- `magicos-original.py` retained as a source reference, not executed in the APK.

## Important limitations

This is a **UI integration**, not a complete conversion of the Python backend. Features requiring `/api/unlock`, `/api/server-state`, the Flask Penalty service, or other server endpoints may not work in the offline WebView. Penalty is marked unavailable instead of faking a running server. External Font Awesome / Google Fonts need internet and may not load offline. No audio/video assets were provided in the source upload. This build has **not** been compiled or tested on an Android device.

## Build

Push this source to your existing GitHub repository and use `.github/workflows/android-build.yml`. The original Java login screen was deliberately not visually modified.
