# MinhQuan v0.5 (Android)

Native Android project derived from TX-MD5-Analyzer Smart; unchanged package ID `com.txanalyzer` so Android can install it as an update.

## UI changes in v0.5

- Uses the supplied green hooded mask image (1000080922.png) as launcher icon, dashboard icon, floating bubble icon and startup avatar.
- Startup has a small dark **174dp × 100dp** loading popup centered against a black screen with a bronze **MINHQUAN** wordmark behind it, based on the supplied reference.
- Round avatar in popup rotates for **3 seconds**; afterward the existing small **MinhQuan'z** key dialog opens.
- The visible phrase `Loading data from Server...` matches the reference but is *decorative only*. No network connection, download, or remote key check takes place.
- App theme uses dark launch background to reduce white flashing on Android 12+.
- Demo key remains `FreeKey_MinhQuan` (tap Get Key to fill), no real licensing/activation.
- Existing user-consented screen capture, OCR, history reading and floating bubble have not been intentionally changed.

## Build APK on GitHub Actions

In Termux after putting this zip in Downloads:

```bash
cd ~/TX-MD5-Analyzer/TX-MD5-Analyzer
git pull --ff-only origin main
unzip -o ~/storage/downloads/MinhQuan-Android-v0.5-source.zip -d .
git add .
git commit -m "MinhQuan v0.5 compact loading and green avatar"
git push origin main
```

Go to `https://github.com/quanminh2089-blip/TX-MD5-Analyzer/actions`, open the latest run, download artifact `TX-MD5-Analyzer-debug` if it succeeds.

## Limitations

This ZIP contains source files; it is not an APK. No local Android SDK was available to compile or test it. A GitHub Actions build and on-device test are required. OCR-based statistics cannot predict fair random game outcomes or reveal an unknown MD5 preimage.
