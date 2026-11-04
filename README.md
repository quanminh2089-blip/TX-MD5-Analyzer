# TX MD5 Analyzer (experimental)
Native Android Java app: user-consented screen capture, draggable overlay, ML Kit OCR, local-only descriptive counts. No website login, interception, betting automation or claim to predict MD5 outcomes.

## Build on GitHub
Create a repository, upload all project files including `.github/workflows/android-build.yml`, then run Actions > Build Android APK > Run workflow. Download artifact `TX-MD5-Analyzer-debug` and install the contained APK.

## Limitations
- Experimental untested project; OCR may pick up unrelated numbers. It cannot reliably parse the screenshot's sideways orientation or black/white history dots yet.
- OCR is only a prototype and must be calibrated with real screenshots before trusting any numbers.
- The app requests consent on each capture session. No screen data is uploaded by app code.
- Build requires Google Maven / ML Kit dependency downloads.
