# MinhQuan + OniRoai v0.8 (Godot 4.5.1)

**One APK**: MinhQuan startup/key -> username/password -> real OniRoai 0.5.0 boot -> playable game.

- Key: `FreeKey_MinhQuan`
- Local demo user: `MinhQuan08`
- Local demo password: `08112008ok`
- The game source and assets come from the supplied OniRoai 0.5.0 Godot ZIP.
- The old native Android TX-MD5-Analyzer project is **not** bundled: this is a unified Godot app to run the game in-process.
- **Android notification from native MinhQuan v0.7 is not yet ported**; Godot needs a native Android plugin for that. No misleading notification claim.
- The UI is an offline demo, not secure account authentication. Key and password are stored in readable client source; use a server for production.
- The loading line is decorative; no server connections are made.

## Build
Open in Godot 4.5.1 and install Android export templates, configure Android SDK/JDK, then Project > Export > Android.
Or push the project files to GitHub and use the included workflow to export debug APK. For large files, Git LFS may be needed.
