<div align="center">

# 🚀 Morphe AutoBuilds

[![Upstream Check](https://img.shields.io/github/actions/workflow/status/YOUR_USERNAME/morphe-autobuilds/check-upstream.yml?label=Upstream%20Check&style=for-the-badge&color=2ea44f)](https://github.com/YOUR_USERNAME/morphe-autobuilds/actions/workflows/check-upstream.yml)
[![Build Status](https://img.shields.io/github/actions/workflow/status/YOUR_USERNAME/morphe-autobuilds/build.yml?label=Build%20Status&style=for-the-badge&color=0366d6)](https://github.com/YOUR_USERNAME/morphe-autobuilds/actions/workflows/build.yml)
[![Latest Release](https://img.shields.io/github/v/release/YOUR_USERNAME/morphe-autobuilds?style=for-the-badge&label=Latest%20Release&color=orange)](https://github.com/YOUR_USERNAME/morphe-autobuilds/releases/latest)
[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

<p align="center">
  <strong>Automated YouTube & YouTube Music APK Builder</strong><br>
  Official Morphe + Anddea Patches • GitHub Actions Powered • JST-Tagged Releases
</p>

<p align="center">
  A sophisticated, automated pipeline that builds ready-to-install YouTube and YouTube Music APKs with Official Morphe and Anddea patches. This system automatically monitors upstream releases, downloads base APKs, applies patches, and publishes optimized arm64-v8a builds with integrated release notes.
</p>

[![View Latest Release](https://img.shields.io/badge/View%20Latest%20Release-0A0A0A?style=flat&logo=github&logoColor=white)](https://github.com/YOUR_USERNAME/morphe-autobuilds/releases/latest)
[![Report Bug](https://img.shields.io/badge/Report%20Bug-0A0A0A?style=flat&logo=github&logoColor=white)](https://github.com/YOUR_USERNAME/morphe-autobuilds/issues)
[![View Docs](https://img.shields.io/badge/View%20Docs-0A0A0A?style=flat&logo=github&logoColor=white)](./IMPLEMENTATION.md)

</div>

---

## ⚡ Quick Start

> **Note:** All APKs are automatically built when Official Morphe or Anddea releases a new version. Releases are tagged with JST timestamps (e.g., `2026-04-21_15-30-JST`).

### 📥 Download Latest APKs

| App | Morphe | Anddea |
| :--- | :--- | :--- |
| **YouTube** | [Download](https://github.com/YOUR_USERNAME/morphe-autobuilds/releases/latest) | [Download](https://github.com/YOUR_USERNAME/morphe-autobuilds/releases/latest) |
| **YouTube Music** | [Download](https://github.com/YOUR_USERNAME/morphe-autobuilds/releases/latest) | [Download](https://github.com/YOUR_USERNAME/morphe-autobuilds/releases/latest) |

### 📱 Supported Configuration

| App | Patch Source | Architecture |
| :--- | :--- | :--- |
| **YouTube** | Official Morphe | arm64-v8a |
| **YouTube** | Anddea | arm64-v8a |
| **YouTube Music** | Official Morphe | arm64-v8a |
| **YouTube Music** | Anddea | arm64-v8a |

---

## ✨ Key Features

* **Upstream-Triggered Builds:** Automatically detects when Official Morphe or Anddea releases a new version and triggers builds immediately.
* **Integrated Release Strategy:** All APKs are released together with a single JST-timestamped tag, ensuring consistency across all builds.
* **Smart Patch Control:** Text-based patch filter files allow precise inclusion or exclusion of specific patches per app/source combination.
* **Optimized Architecture:** arm64-v8a only for modern Android devices, reducing file size while maintaining compatibility.
* **Automated Release Notes:** README.md and detailed release notes are automatically generated with version info and update status.
* **GitHub Actions Powered:** Zero manual intervention required—everything runs on GitHub's infrastructure.
* **Reproducible Builds:** Previous APK versions are preserved in release history, allowing users to downgrade if needed.

---

## 📋 System Architecture

### Workflow Components

```
┌─────────────────────────────────────────────────────────────┐
│ check-upstream.yml (Daily 6:00 UTC)                         │
│ - Fetch latest Morphe & Anddea tags                         │
│ - Compare with stored Variables                             │
│ - Trigger build.yml if updates found                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ build.yml (Triggered on upstream update)                    │
│ - Download Morphe & Anddea tools                            │
│ - Build 4 APK combinations in parallel                      │
│ - Generate README.md                                        │
│ - Create JST-timestamped release                            │
└─────────────────────────────────────────────────────────────┘
```

### Build Matrix

The system builds 4 APK combinations automatically:

1. YouTube × Official Morphe
2. YouTube × Anddea
3. YouTube Music × Official Morphe
4. YouTube Music × Anddea

---

## 🛠️ Repository Structure

```
morphe-autobuilds/
├── .github/workflows/
│   ├── check-upstream.yml      # Upstream monitoring workflow
│   └── build.yml               # Build & release workflow
├── apps/apkmirror/
│   ├── youtube.json            # YouTube APKMirror config
│   └── youtube-music.json      # YouTube Music APKMirror config
├── patches/
│   ├── youtube-morphe.txt
│   ├── youtube-revanced-anddea.txt
│   ├── youtube-music-morphe.txt
│   └── youtube-music-revanced-anddea.txt
├── scripts/
│   └── generate_readme.py      # README.md auto-generation script
├── sources/
│   ├── morphe.json             # Morphe tool sources
│   └── revanced-anddea.json    # Anddea tool sources
├── src/                        # Core build logic (Python)
├── my-patch-config.json        # Target apps & sources
├── arch-config.json            # Architecture configuration
├── IMPLEMENTATION.md           # Implementation details
├── SETUP.md                    # Setup instructions
└── README.md                   # This file
```

---

## ⚙️ Configuration Guide

### 1. Target Apps (`my-patch-config.json`)

Define which app/source combinations to build:

```json
{
  "patch_list": [
    { "app_name": "youtube", "source": "morphe" },
    { "app_name": "youtube", "source": "revanced-anddea" },
    { "app_name": "youtube-music", "source": "morphe" },
    { "app_name": "youtube-music", "source": "revanced-anddea" }
  ]
}
```

### 2. Architecture (`arch-config.json`)

Specify target architectures:

```json
{
  "youtube": { "arch": ["arm64-v8a"] },
  "youtube-music": { "arch": ["arm64-v8a"] }
}
```

### 3. Patch Filters

Located in `patches/`. Use `-` to exclude patches and `+` to force include:

**Example: `patches/youtube-revanced-anddea.txt`**
```text
# YouTube × Anddea patch rules
- Custom branding name for YouTube
- Custom branding icon for YouTube
```

### 4. APK Sources

Located in `apps/apkmirror/`. Example for YouTube:

```json
{
  "org": "google-inc",
  "name": "youtube",
  "type": "APK",
  "arch": "universal",
  "dpi": "nodpi",
  "package": "com.google.android.youtube",
  "version": ""
}
```

---

## 🚀 Getting Started

### Prerequisites

* GitHub repository with Actions enabled
* GitHub CLI (`gh`) installed
* Python 3.11+

### Setup Instructions

See [SETUP.md](./SETUP.md) for detailed setup instructions, including:

1. Repository Variables initialization
2. GitHub Actions configuration
3. Manual testing procedures
4. PAT (Personal Access Token) setup
5. Troubleshooting guide

**Quick setup:**
```bash
# Initialize Variables
gh variable set LAST_MORPHE_TAG --body "v1.13.2"
gh variable set LAST_ANDDEA_TAG --body "v5.4.0-all"

# Test build workflow
gh workflow run build.yml

# Test upstream check
gh workflow run check-upstream.yml
```

---

## 📚 Documentation

* **[IMPLEMENTATION.md](./IMPLEMENTATION.md)** - Detailed implementation documentation
* **[SETUP.md](./SETUP.md)** - Complete setup and configuration guide
* **[Design Document](./morphe-autobuild-設計書_v2.docx)** - Original design specification (Japanese)

---

## 🔄 Release Tagging

Releases are tagged with JST timestamps in the format: `YYYY-MM-DD_HH-MM-JST`

**Example:** `2026-04-21_15-30-JST`

Each release includes:
- 4 APK files (YouTube/YTMusic × Morphe/Anddea)
- README.md with installation instructions
- Detailed release notes with version information

---

## 🔗 Patch Sources

* **Official Morphe**: https://github.com/MorpheApp/morphe-patches
* **Anddea**: https://github.com/anddea/revanced-patches

---

## 📥 Installation Instructions

1. Download the desired APK from the latest release
2. Enable "Unknown sources" on your Android device
3. Uninstall the existing YouTube/YouTube Music app
4. Install the downloaded APK
5. (Optional) Install MicroG-RE for full functionality

---

## ⚠️ Disclaimer

* These APKs are built automatically using official Morphe and Anddea tools
* **Not officially affiliated** with Morphe or Anddea teams
* Use at your own risk
* MicroG-RE may be required for full functionality
* Always backup your data before installing modified APKs

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch
3. Test your changes locally
4. Submit a pull request

---

## 📞 Support

For issues or questions:

1. Check [SETUP.md](./SETUP.md) troubleshooting section
2. Review [IMPLEMENTATION.md](./IMPLEMENTATION.md) for technical details
3. Open an issue on GitHub

---

<div align="center">

**If you found this project helpful, please consider giving it a ⭐ Star.**

Made with 💜 by the Morphe AutoBuilds Community

</div>
