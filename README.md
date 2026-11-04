# MinhQuan — Android v0.3 (Source)

Native Android Java app, from TX-MD5-Analyzer Smart v0.2.

## Startup / icon
- Launcher icon and round avatar: exact mask image supplied by the user, centered/cropped as an Android image resource.
- Animated splash: circular avatar rotating for **3 seconds**, then a small dark key window **centered within the app** (not a third-party floating permission overlay).
- Free **offline demo key**: `FreeKey_MinhQuan`; tap **Lấy key** to auto-fill, then tap **XÁC NHẬN**. This local UI demo is **not** secure authentication, does not contact a server, and is not a subscription/license system.
- After that: start screen-reading, stop, or open the history-reading bubble with user-granted Android overlay and MediaProjection permissions.
- The capture service remains the Smart v0.2 automatic history reader (ML Kit OCR and chip detection).

## Android privacy and limitations
- Only captures after user manually approves Android screen-sharing permissions.
- No login to the game, network/key checking, or app-injection. No automated betting.
- Recognizes past visible results. No guarantee it predicts future dice outcomes from MD5.
- The screen-rotation/detection logic needs device testing, and real APK compilation has not been verified here.

## Build APK using GitHub Actions
Unzip this archive into the root of your existing `TX-MD5-Analyzer` Git repository, overwriting old project files. Then run `git add . && git commit -m "Add MinhQuan splash and login UI" && git push origin main`. In GitHub > Actions > `Build Android APK`, download artifact `MinhQuan-debug` if the workflow is green.
