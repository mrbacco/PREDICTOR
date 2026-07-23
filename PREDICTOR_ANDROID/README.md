<!--
Author: mrbacco04@gmail.com
Month: July 2026
Release Version: 1.0.0
License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
-->
# Irish Lotto Predictor for Android

`PREDICTOR_ANDROID` is a standalone native Android project built with Kotlin and
Jetpack Compose. It does not need or import the Python web application.

## Android Studio

1. Install the current stable Android Studio.
2. Select **Open** and choose the `PREDICTOR_ANDROID` folder, not the parent repository.
3. Allow Android Studio to install Android SDK 36 and its suggested JDK 17 runtime.
4. Wait for the Gradle sync to complete.
5. Create an Android emulator or connect a phone with USB debugging enabled.
6. Select the `app` run configuration and press **Run**.

The application supports Android 8.0 (API 26) and newer.

## Command Line

After Android Studio has installed the Android SDK and JDK, run these commands from
the `PREDICTOR_ANDROID` folder:

```powershell
.\gradlew.bat test
.\gradlew.bat assembleDebug
```

The debug APK is written to:

```text
app/build/outputs/apk/debug/app-debug.apk
```

Install it on a connected phone with:

```powershell
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

## Data And Privacy

- The bundled draw history is copied to private app storage on first launch.
- Predictions work offline and default to five lines with 50,000 iterations.
- **Refresh data** is the only action that contacts `lottery.ie`.
- The app does not request an account, contacts, location, or storage permissions.
- Runtime events use the `BAC_LOG` tag in Android Studio's Logcat window.

## Random Seed

The seed makes a run reproducible. The same Android app version, dataset, settings,
and seed produce the same lines. **New seed** changes the seed and immediately runs
the predictor again, producing a different random sequence.

## Licensing

The standalone project includes Apache 2.0, GNU AGPL v3, and commercial licensing
paths. See `LICENSE-APACHE`, `LICENSE-AGPL`, and `COMMERCIAL-LICENSE.md`.
