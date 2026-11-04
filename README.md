# TX MD5 Analyzer — Smart History Reader v0.2 (Android)

This is a native Android proof-of-concept. Its screen-capture foreground service uses Android MediaProjection **with explicit user consent**, locally running ML Kit OCR, and a game-layout-specific chip detector (white = Xỉu, gold = Tài). No game login, injection, interception, transmission or betting automation is included.

## What changed
- A small draggable TX floating bubble; tap to expand results, tap heading to collapse, or use Stop.
- Auto-orients portrait screenshots of sideways landscape games by trying -90°/90° (and landscape 0°/180°) during OCR.
- Detects the game panel containing **LỊCH SỬ PHIÊN**; scans the visible history-board gold/white chip grid in column order (20 columns × 5 rows) and attempts an additional enlarged OCR pass for the number inside each chip.
- Parses displayed aggregate counts `Tài:27` / `Xỉu:23` when recognizable; these refer to the game's reported larger summary and are not assumed to equal visible-grid chip counts.
- Shows `T`/`X` for the chip's class, plus the number only when OCR confirms a plausible value consistent with the chip color. `?` means no confident OCR reading.
- On-screen updates are automatic roughly every 1.7 seconds (longer if OCR takes time); no guarantee of instantaneous or correct OCR on every device.
- Refreshes screen capture dimensions when device orientation changes, without attempting another createVirtualDisplay on the same projection token.

## Build with GitHub Actions
Copy the project files into the root of your existing GitHub repository (including `.github/workflows/android-build.yml`) and push to `main`. `Build Android APK` runs `gradle :app:assembleDebug`; download the `TX-MD5-Analyzer-debug` artifact if successful.

## Known limits
- **Not tested as an APK on a physical Android phone.** Compile/run must be verified in GitHub Actions and on the user's device.
- History chip geometry is calibrated to the provided screenshot at 1536×691 in landscape orientation. On different game skins, browsers or screen aspect ratios it may not detect the grid. It deliberately reports low-confidence detection instead of manufacturing values.
- Text OCR may miss small values and summary labels or mistake game labels for text. Number recognition requires manual validation against the game.
- A screenshot of a historical result cannot predict future results from a cryptographic hash or a properly random backend. This is a **descriptive history reader, not a next-round predictor or wagering signal**.
- Capturing screen content involves sensitive information. Do not run with other private apps visible. Screen capture ends when service stops.
