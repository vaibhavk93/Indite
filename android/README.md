# indite speed test (Android)

Test APK: is the Hinglish model fast enough on a phone, fully offline? Based on whisper.cpp's Android example.
"Run 15-min test" transcribes every piece in `app/src/main/assets/samples/` and reports speed, battery temperature and peak memory.

Build (from the repo root, after `sh scripts/setup_local.sh`):
1. Put the model at `android/app/src/main/assets/models/ggml-apex-q5_0.bin` and 16 kHz mono WAV pieces in `assets/samples/` (never committed: private audio).
2. Needs Java 17, Android SDK platform 34, NDK 25.2.9519653, CMake 3.22.1.
3. `cd android && ./gradlew assembleRelease` -> `app/build/outputs/apk/release/app-release.apk`
   Behind a company HTTPS proxy, give Java a trust store holding the Mac's certificates (JAVA_TOOL_OPTIONS=-Djavax.net.ssl.trustStore=...).

---

A sample Android app using [whisper.cpp](https://github.com/ggerganov/whisper.cpp/) to do voice-to-text transcriptions.

To use:

1. Select a model from the [whisper.cpp repository](https://github.com/ggerganov/whisper.cpp/tree/master/models).[^1]
2. Copy the model to the "app/src/main/assets/models" folder.
3. Select a sample audio file (for example, [jfk.wav](https://github.com/ggerganov/whisper.cpp/raw/master/samples/jfk.wav)).
4. Copy the sample to the "app/src/main/assets/samples" folder.
5. Select the "release" active build variant, and use Android Studio to run and deploy to your device.
[^1]: I recommend the tiny or base models for running on an Android device.

(PS: Do not move this android project folder individually to other folders, because this android project folder depends on the files of the whole project.)

<img width="300" alt="image" src="https://user-images.githubusercontent.com/1670775/221613663-a17bf770-27ef-45ab-9a46-a5f99ba65d2a.jpg">
