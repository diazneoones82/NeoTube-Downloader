# NeoTube Downloader for iOS

This folder contains the iOS client app for NeoTube Downloader. It is a native SwiftUI shell around the NeoTube web UI using `WKWebView`, branded as Neo Apps.

## What This App Does

- Opens a NeoTube Downloader server URL in a native iOS app.
- Injects `window.NeoTubeIOS` so the web UI can brand the footer as `NEO Apps : iOS`.
- Stores the last server URL in iOS `UserDefaults`.
- Provides a small setup screen when no server URL has been configured.

## Build Requirements

- macOS with Xcode 15 or newer.
- An Apple Developer account/team if you want to install on a physical iPhone.
- A reachable NeoTube Downloader backend, for example the Windows desktop app or a server running on your LAN.

## Build

Open the project in Xcode:

```bash
open ios/NeoTubeDownloader.xcodeproj
```

Then:

1. Select the `NeoTubeDownloader` target.
2. Set your signing team.
3. Choose an iPhone simulator or a connected iPhone.
4. Press **Run**.

For command-line archive builds on macOS:

```bash
xcodebuild \
  -project ios/NeoTubeDownloader.xcodeproj \
  -scheme NeoTubeDownloader \
  -configuration Release \
  -destination 'generic/platform=iOS' \
  archive \
  -archivePath build/NeoTubeDownloader.xcarchive
```

Exporting an `.ipa` requires an `ExportOptions.plist` configured for your Apple Developer signing method.

