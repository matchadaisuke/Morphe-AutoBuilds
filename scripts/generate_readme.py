#!/usr/bin/env python3
"""
Generate README.md for Morphe AutoBuilds release
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def generate_readme(build_info: dict, apk_list: list) -> str:
    """
    Generate README.md content for release
    
    Args:
        build_info: Dictionary containing build metadata (timestamp, morphe_tag, anddea_tag, etc.)
        apk_list: List of APK file information
    
    Returns:
        Formatted README.md content
    """
    
    timestamp = build_info.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M JST'))
    morphe_tag = build_info.get('morphe_tag', 'unknown')
    anddea_tag = build_info.get('anddea_tag', 'unknown')
    morphe_updated = build_info.get('morphe_updated', False)
    anddea_updated = build_info.get('anddea_updated', False)
    
    # Build APK table
    apk_table_rows = []
    for apk in apk_list:
        apk_table_rows.append(
            f"| {apk['filename']} | {apk['app']} | {apk['source']} | {apk['version']} |"
        )
    apk_table = "\n".join(apk_table_rows)
    
    # Build update status table
    morphe_status = "✅ 更新あり" if morphe_updated else "⏸️ 変更なし（前回APK流用）"
    anddea_status = "✅ 更新あり" if anddea_updated else "⏸️ 変更なし（前回APK流用）"
    
    readme = f"""# Morphe AutoBuilds

## 🚀 Morphe AutoBuilds - {timestamp}

## 📦 添付APK一覧

| ファイル名 | アプリ | パッチソース | パッチバージョン |
| --- | --- | --- | --- |
{apk_table}

## 🔄 今回の更新内容

| パッチソース | 前回バージョン | 今回バージョン | 変更有無 |
| --- | --- | --- | --- |
| Official Morphe | - | {morphe_tag} | {morphe_status} |
| Anddea | - | {anddea_tag} | {anddea_status} |

## 🔗 パッチソース

- **Official Morphe**: [https://github.com/MorpheApp/morphe-patches/releases/latest](https://github.com/MorpheApp/morphe-patches/releases/latest)
- **Anddea**: [https://github.com/anddea/revanced-patches/releases/latest](https://github.com/anddea/revanced-patches/releases/latest)

## 📱 インストール方法

1. 対象APKをダウンロード
2. 端末で「提供元不明のアプリ」を許可
3. 既存のYouTube/YouTube Musicをアンインストール
4. APKをインストール

## ⚠️ 注意事項

- 全APKは arm64-v8a アーキテクチャ専用です
- インストール前に既存アプリをアンインストールしてください
- 本APKは自動ビルドされています。自己責任でご利用ください

## 📋 ビルド情報

- **ビルド日時**: {timestamp}
- **Official Morphe**: {morphe_tag}
- **Anddea**: {anddea_tag}
"""
    
    return readme


def main():
    """Main entry point"""
    
    # Read build info from environment or arguments
    if len(sys.argv) > 1:
        build_info_file = sys.argv[1]
        with open(build_info_file, 'r') as f:
            build_info = json.load(f)
    else:
        # Default build info
        build_info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M JST'),
            'morphe_tag': 'v1.13.2',
            'anddea_tag': 'v5.4.0-all',
            'morphe_updated': True,
            'anddea_updated': False,
        }
    
    # Read APK list from environment or arguments
    if len(sys.argv) > 2:
        apk_list_file = sys.argv[2]
        with open(apk_list_file, 'r') as f:
            apk_list = json.load(f)
    else:
        # Default APK list
        apk_list = [
            {
                'filename': 'youtube-morphe-v1.13.2.apk',
                'app': 'YouTube',
                'source': 'Official Morphe',
                'version': 'v1.13.2'
            },
            {
                'filename': 'youtube-revanced-anddea-v5.4.0-all.apk',
                'app': 'YouTube',
                'source': 'Anddea',
                'version': 'v5.4.0-all'
            },
            {
                'filename': 'youtube-music-morphe-v1.13.2.apk',
                'app': 'YouTube Music',
                'source': 'Official Morphe',
                'version': 'v1.13.2'
            },
            {
                'filename': 'youtube-music-revanced-anddea-v5.4.0-all.apk',
                'app': 'YouTube Music',
                'source': 'Anddea',
                'version': 'v5.4.0-all'
            },
        ]
    
    readme_content = generate_readme(build_info, apk_list)
    
    # Output to stdout or file
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    if output_file:
        with open(output_file, 'w') as f:
            f.write(readme_content)
        print(f"✅ README.md generated: {output_file}")
    else:
        print(readme_content)


if __name__ == '__main__':
    main()
