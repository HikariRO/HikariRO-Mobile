# HikariRO Mobile

Private Android prototype for running the Windows HikariRO client through a
customized Winlator environment.

The APK does not bundle the game client. On first launch it downloads
`HikariRO Full.zip` from the official HikariRO website, resumes interrupted
downloads, extracts the client, creates a 960x540 container, and starts
`raghikari.exe`.

## Test target

- Samsung Galaxy A25 5G
- Android 16
- 8 GB RAM
- Mali-G68 GPU

## Build

GitHub Actions builds a private debug-signed ARM64 APK from the official
Winlator source and applies the HikariRO customization during CI.

Winlator and the retained upstream code are licensed under LGPL-2.1.
