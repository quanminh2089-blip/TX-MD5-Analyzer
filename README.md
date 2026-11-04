# MinhQuan v1.1 – Key-only + One-switch Overlay + Gesture Test

## Requested UI changes
- Removed Matrix Terminal, simulated ports, and redundant account/password login screen.
- On opening: enter offline key `FreeKey_MinhQuan` once (saved locally). The key is *not* secure license protection.
- If overlay permission is not granted, open Android system permission settings.
- Once permission granted: start small overlay and try to open Liên Quân Mobile VN (`com.garena.game.kgvn`).
- The floating overlay displays only a draggable `AUTO CHƠI • TẮT/BẬT` button.

## What AUTO CHƠI actually does
- If permission for the **MinhQuan điều khiển** Accessibility service is missing, tapping AUTO opens Android Accessibility settings. You must enable the service manually.
- When Liên Quân is foreground and landscape, tapping AUTO enables a **90-second control test**: periodic approximate attack taps and occasional short movement gestures, in the game only. Tap again to stop immediately. It stops when the game loses foreground or the service disconnects.
- **This is not a bot that wins or plays a whole match.** No visual recognition, enemy detection, ML, genuine strategy or game-data access is implemented. The existing BotCore remains available but does not receive actual observations. Repetitive touches are not the same as AI gameplay.
- The approximate joystick / attack coordinates depend on the game's HUD and display settings; test only in training mode. Wrong coordinates may click unintended controls. In-game anti-cheat and terms of service may prohibit automation.
- No screen recording, root, background data collection, or network upload is performed.

## Build
Android 15 / no root. GitHub Actions `.github/workflows/android-build.yml` builds with Java 17 / Gradle 8.9 / SDK 35. The project includes Android native Java sources, **not a prebuilt APK**. Build has not been run in this environment.

## How to test
1. Install debug APK and open MinhQuan. Enter key.
2. Allow 'Hiển thị trên ứng dụng khác'. The app opens Liên Quân automatically if installed.
3. Enter **practice/training** and tap the floating button. Android will direct you to Accessibility settings on first use; enable `MinhQuan điều khiển`, then return to the training match.
4. Tap once to turn on test movements and attacks; tap again to turn off. It also stops after 90 seconds.
5. The overlay itself can be dragged; it contains no Matrix panel or other controls.
