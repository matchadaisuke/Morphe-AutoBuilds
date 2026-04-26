# Morphe AutoBuilds - 実装ドキュメント

## 📋 概要

このドキュメントは、設計書 v2.0 に基づいて実装された Morphe AutoBuilds システムの詳細を記載しています。

## 🎯 実装内容

### 1. 新規設定ファイル

#### `my-patch-config.json`
YouTube / YouTube Music を対象に、Official Morphe と Anddea のパッチソースの組み合わせを定義。

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

#### `arch-config.json`
arm64-v8a アーキテクチャのみビルド対象に指定。

```json
{
  "youtube": { "arch": ["arm64-v8a"] },
  "youtube-music": { "arch": ["arm64-v8a"] }
}
```

### 2. パッチフィルタファイル

#### `patches/youtube-morphe.txt`
YouTube × Official Morphe パッチの設定（現在は空）

#### `patches/youtube-revanced-anddea.txt`
YouTube × Anddea パッチの除外ルール
- Custom branding name for YouTube
- Custom branding icon for YouTube

#### `patches/youtube-music-revanced-anddea.txt`
YouTube Music × Anddea パッチの除外ルール
- AddResourcesPatch

#### `patches/youtube-music-morphe.txt`
既存ファイルを確認（-AddResourcesPatch が設定済み）

### 3. スクリプト

#### `scripts/generate_readme.py`
リリース用の README.md を自動生成するスクリプト。以下の情報を含める：
- ビルド日時（JST）
- 添付APK一覧
- パッチソースのバージョン
- 更新有無
- インストール方法
- 注意事項

使用方法：
```bash
python scripts/generate_readme.py [build_info.json] [apk_list.json] [output.md]
```

### 4. GitHub Actions ワークフロー

#### `.github/workflows/check-upstream.yml`
**役割**: Morphe / Anddea の upstream を監視し、更新があればビルドをトリガー

**スケジュール**: 毎日 6:00 UTC（cron）

**処理フロー**:
1. MorpheApp/morphe-patches の最新タグを取得
2. anddea/revanced-patches の最新タグを取得
3. リポジトリ Variables（LAST_MORPHE_TAG / LAST_ANDDEA_TAG）と比較
4. 差分があれば build.yml をトリガー
5. Variables を新タグで更新

**必要な権限**:
- `contents: write` - Variables 更新用
- `actions: write` - workflow_dispatch 発火用

#### `.github/workflows/build.yml`
**役割**: ビルドを実行し、JST 日時タグで統合リリース

**トリガー**:
- `check-upstream.yml` からの workflow_dispatch
- 手動実行（workflow_dispatch）

**処理フロー**:
1. Morphe CLI / Patches をダウンロード
2. ReVanced CLI（inotia00 fork） / Anddea Patches をダウンロード
3. `my-patch-config.json` から matrix を生成
4. 並列でビルド実行（4 コンボ）
5. JST 日時タグで統合リリース作成
6. 全 APK + README.md をアップロード

**出力**:
- リリースタグ形式: `YYYY-MM-DD_HH-MM-JST`
- 例: `2026-04-21_15-30-JST`

### 5. 既存ファイル（変更なし）

以下のファイルは既存コードをそのまま使用：
- `src/__main__.py` - ビルドコアロジック
- `src/downloader.py` - APK ダウンロード
- `src/utils.py` - ユーティリティ関数
- `sources/morphe.json` - Morphe ソース設定
- `sources/revanced-anddea.json` - Anddea ソース設定

## 🔄 ワークフロー実行フロー

### 通常実行（upstream 更新検知時）

```
1. check-upstream.yml (cron 6:00 UTC)
   ↓
2. GitHub API で最新タグ取得
   ↓
3. Variables と比較
   ↓
4. 差分あり → build.yml をトリガー
   ↓
5. build.yml
   - ツールダウンロード
   - matrix 生成
   - 並列ビルド（4 コンボ）
   - JST 日時タグでリリース作成
   ↓
6. GitHub Release に APK + README.md を公開
```

### 手動実行

```
1. GitHub UI で build.yml を手動トリガー
   ↓
2. 入力パラメータ（morphe_tag, anddea_tag など）を指定
   ↓
3. ビルド実行 → リリース作成
```

## 📝 APK 命名規則

形式: `{アプリ名}-{パッチ名}-{パッチタグ名}.apk`

例:
- `youtube-morphe-v1.13.2.apk`
- `youtube-revanced-anddea-v5.4.0-all.apk`
- `youtube-music-morphe-v1.13.2.apk`
- `youtube-music-revanced-anddea-v5.4.0-all.apk`

## 🔗 リリースノート仕様

リリースノートには以下の情報を含める：

1. **ビルド日時** (JST)
2. **添付APK一覧** (テーブル形式)
3. **今回の更新内容** (パッチソースごとの更新有無)
4. **パッチソース URL**
5. **注意事項**

## ⚠️ 注意点

### 1. GitHub Variables の設定
`check-upstream.yml` から Variables を更新するには、リポジトリの Actions secrets に PAT（Personal Access Token）を登録する必要がある場合があります。

**対処**:
1. GitHub で PAT を生成（repo スコープ）
2. リポジトリの Settings → Secrets and variables → Actions secrets に `PAT_TOKEN` として登録
3. ワークフロー内で `GH_TOKEN: ${{ secrets.PAT_TOKEN }}` として使用

### 2. Morphe CLI の引数仕様
`src/__main__.py` のコメントに「Morphe CLI might have different arguments」とあるため、実際のビルド実行時に CLI の出力を確認し、必要に応じて修正が必要な場合があります。

### 3. 前回 APK 再利用
設計書では「前回リリースのAPKを再利用」とありますが、現在の実装では毎回全コンボをビルドしています。最適化が必要な場合は、以下の処理を追加してください：

```bash
# 前回のリリースから該当APKをダウンロード
gh release list --limit 2 | tail -1 | awk '{print $1}' > prev_tag.txt
gh release download $(cat prev_tag.txt) --pattern "youtube-revanced-anddea-*.apk"
```

## 📊 ファイル変更サマリ

| ファイル | 種別 | 説明 |
| --- | --- | --- |
| my-patch-config.json | 新規 | YouTube/YTMusic × Morphe/Anddea の4エントリ |
| arch-config.json | 変更 | arm64-v8a のみビルド設定 |
| patches/youtube-morphe.txt | 新規 | YouTube × Morphe パッチ設定 |
| patches/youtube-revanced-anddea.txt | 新規 | YouTube × Anddea パッチ除外ルール |
| patches/youtube-music-revanced-anddea.txt | 新規 | YouTube Music × Anddea パッチ除外ルール |
| scripts/generate_readme.py | 新規 | README.md 自動生成スクリプト |
| .github/workflows/check-upstream.yml | 新規 | upstream 監視ワークフロー |
| .github/workflows/build.yml | 新規 | ビルド・リリースワークフロー |
| .github/workflows/patch.yml | 廃止予定 | 既存の cron トリガーワークフロー（置き換え） |

## 🚀 次のステップ

1. **リポジトリに push**: 新規ファイルをリポジトリに push
2. **Variables 初期化**: リポジトリ Settings で LAST_MORPHE_TAG / LAST_ANDDEA_TAG を初期値で設定
3. **手動テスト**: build.yml を手動トリガーして、4つのAPKが正しく生成・リリースされるか確認
4. **check-upstream.yml テスト**: workflow_dispatch で手動実行して、差分検知が動くか確認
5. **PAT_TOKEN 設定**: 必要に応じて GitHub Actions secrets に PAT を登録
6. **patch.yml 削除**: 既存の cron トリガーワークフローを削除（またはコメントアウト）

## 📚 参考資料

- [設計書 v2.0](morphe-autobuild-設計書_v2.docx)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
