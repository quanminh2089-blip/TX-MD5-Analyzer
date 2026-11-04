# MinhQuan v1.0 - Bot decision core (prototype)

This is a real deterministic decision engine, not an autonomous Liên Quân bot.
It does not capture screens, recognize champions, dispatch gestures by itself, or hook game memory. The separate AutoControl module implements a basic opt-in gesture TEST; it is not connected to game-state perception.

## Included
- `BotCore.java`: prioritizes stop/wait, stale-frame rejection, confidence gating, survival, shopping, visible combat, farming, pushing, lane return.
- `BotSession.java`: explicit disabled-by-default gate.
- `tests/BotCoreTest.java`: six JVM tests without Android SDK.

## Run tests (Termux with Java installed)
`mkdir -p /tmp/mqbotclasses && javac -d /tmp/mqbotclasses app/src/main/java/com/txanalyzer/bot/*.java tests/BotCoreTest.java && java -cp /tmp/mqbotclasses BotCoreTest`

## Not yet implemented
Screen capture, computer vision, game-state calibration, connection between live observations and control actions, live match testing.
No guarantee of full-match gameplay or compatibility with anti-cheat.

## Important
Input observations must come from a verified source; do not fabricate hidden enemy positions.
