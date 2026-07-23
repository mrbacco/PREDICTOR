# Release Preparation and Publishing Plan

This plan outlines the steps required to build a production-ready Android App Bundle (AAB) and the process for publishing it to the Google Play Store.

## User Review Required

> [!IMPORTANT]
> **Signing Credentials**: You will need to generate a Keystore file and provide passwords. **Do not share these passwords with me.** I will provide a way to configure them securely using `local.properties`.

> [!NOTE]
> **Google Play Developer Account**: Publishing requires a Google Play Developer account, which has a one-time $25 registration fee.

## Proposed Changes

### 1. Build Configuration
I will update the build configuration to support signing and optimize the release build.

#### [MODIFY] [build.gradle.kts](file:///C:/_PROJECTS/PREDICTOR/PREDICTOR_ANDROID/app/build.gradle.kts)
- Add a `signingConfigs` block.
- Reference signing properties from `local.properties` or environment variables to avoid hardcoding sensitive data.
- Ensure `isMinifyEnabled` and `isShrinkResources` are set to `true` (already done).

### 2. Signing Setup
I will provide a template for `local.properties` that you should fill with your keystore information.

#### [NEW] [release-signing.properties.template](file:///C:/_PROJECTS/PREDICTOR/PREDICTOR_ANDROID/release-signing.properties.template)
- A template file to guide you on which properties are needed (Keystore path, alias, passwords).

---

## Publishing Workflow

### Phase 1: Preparation (Technical)
1. **Generate Keystore**: Use Android Studio's "Generate Signed Bundle / APK" wizard or the `keytool` command.
2. **Configure Signing**: Apply the signing configuration in `build.gradle.kts`.
3. **Build AAB**: Run the Gradle task to generate the `.aab` file.

### Phase 2: Google Play Console (Manual)
1. **Account Setup**: Register for a developer account.
2. **Create App**: Set up the app entry in the Play Console.
3. **Store Listing**: Provide descriptions, screenshots, and icons.
4. **Content Rating**: Complete the questionnaire.
5. **Privacy Policy**: Provide a link to your privacy policy (required if the app uses internet or handles data).
6. **Upload**: Upload the AAB to a testing track (Internal, Alpha, or Beta) first, then promote to Production.

---

## Verification Plan

### Automated Tests
- Run `:app:assembleRelease` to ensure the release build compiles.
- Run `:app:bundleRelease` to ensure the App Bundle can be generated.

### Manual Verification
- Install the release build on a device to verify that minification (R8) hasn't introduced any runtime issues (e.g., missing classes due to reflection).
- Verify the app icon and label are correct on the home screen.
