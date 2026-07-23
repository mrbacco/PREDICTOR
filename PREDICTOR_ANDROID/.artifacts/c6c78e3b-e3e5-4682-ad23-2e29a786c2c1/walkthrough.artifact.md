# Release Configuration Walkthrough

I have configured the project for production releases. This includes setting up signing logic and optimizing the release build.

## Changes Made

### 1. Build Configuration
Updated [build.gradle.kts](file:///C:/_PROJECTS/PREDICTOR/PREDICTOR_ANDROID/app/build.gradle.kts) to:
- Load signing credentials from an external properties file.
- Add a `release` signing configuration.
- Enable minification (R8) and resource shrinking for the release build.
- Added a fallback so the build doesn't fail if signing properties are missing (it will just produce an unsigned bundle).

### 2. Security & Credentials
- Created [release-signing.properties.template](file:///C:/_PROJECTS/PREDICTOR/PREDICTOR_ANDROID/release-signing.properties.template).
- Updated [.gitignore](file:///C:/_PROJECTS/PREDICTOR/PREDICTOR_ANDROID/.gitignore) to ensure `release-signing.properties` is never committed to Version Control.

---

## Next Steps for You

### 1. Generate a Keystore
In Android Studio:
1. Go to **Build > Generate Signed Bundle / APK...**
2. Select **Android App Bundle** and click **Next**.
3. Under **Key store path**, click **Create new...**
4. Fill in the details (path, passwords, alias) and click **OK**.
5. **CRITICAL**: Remember these passwords and keep the `.jks` file safe.

### 2. Configure Signing
1. Copy [release-signing.properties.template](file:///C:/_PROJECTS/PREDICTOR/PREDICTOR_ANDROID/release-signing.properties.template) to a new file named `release-signing.properties` in the project root.
2. Fill in the values with the details from the keystore you just created.

### 3. Build the Signed Bundle
Once configured, run this command in the terminal or use the Gradle tool window:
```powershell
./gradlew :app:bundleRelease
```
The signed `.aab` file will be located in `app/build/outputs/bundle/release/`.

### 4. Upload to Play Console
Upload the generated `.aab` file to the [Google Play Console](https://play.google.com/console).
