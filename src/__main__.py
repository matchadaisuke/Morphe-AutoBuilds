import json
import logging
import re
from sys import exit
from pathlib import Path
from os import getenv
import subprocess
from src import (
    utils,
    downloader
)

def run_build(app_name: str, source: str, arch: str = "universal") -> str:
    """Build APK for specific architecture"""
    download_files, name = downloader.download_required(source)

    logging.info(f"📦 Downloaded {len(download_files)} files for {source}:")
    for file in download_files:
        logging.info(f"  - {file.name} ({file.stat().st_size} bytes)")

    # DETECT SOURCE TYPE
    is_morphe = False
    is_revanced = False

    for file in download_files:
        if "morphe-cli" in file.name.lower():
            is_morphe = True
            break
        elif "revanced-cli" in file.name.lower():
            is_revanced = True
            break

    if not is_morphe and not is_revanced:
        for file in download_files:
            if file.suffix == ".mpp":
                is_morphe = True
                break
            elif file.suffix in [".rvp", ".jar"] and "patches" in file.name.lower():
                is_revanced = True
                break

    if not is_morphe and not is_revanced:
        is_morphe = "morphe" in source.lower() or "custom" in source.lower()
        is_revanced = not is_morphe

    logging.info(f"🔍 Detected: {'Morphe' if is_morphe else 'ReVanced'} source type")

    # FIND FILES
    if is_morphe:
        cli = utils.find_file(download_files, contains="morphe-cli", suffix=".jar", exclude=["dev"])
        if not cli:
            cli = utils.find_file(download_files, contains="morphe", suffix=".jar")
        patches = utils.find_file(download_files, contains="patches", suffix=".mpp")
        if not patches:
            patches = utils.find_file(download_files, suffix=".mpp")
    else:
        cli = utils.find_file(download_files, contains="revanced-cli", suffix=".jar")
        patches = utils.find_file(download_files, contains="patches", suffix=".rvp")
        if not patches:
            patches = utils.find_file(download_files, contains="patches", suffix=".mpp")
        if not patches:
            patches = utils.find_file(download_files, suffix=".mpp")
        if not patches:
            patches = utils.find_file(download_files, contains="patches", suffix=".jar")

    # Validate tools — 見つからなければ即exit(1)
    if not cli:
        logging.error(f"❌ FATAL: CLI jar not found for source '{source}'")
        logging.error(f"   Downloaded files: {[f.name for f in download_files]}")
        exit(1)
    if not patches:
        logging.error(f"❌ FATAL: Patches file not found for source '{source}'")
        logging.error(f"   Downloaded files: {[f.name for f in download_files]}")
        exit(1)

    logging.info(f"✅ Using CLI: {cli.name}")
    logging.info(f"✅ Using patches: {patches.name}")

    download_methods = [
        downloader.download_apkmirror,
        downloader.download_apkpure,
        downloader.download_uptodown,
        downloader.download_aptoide,
    ]

    input_apk = None
    version = None
    tried = []
    for method in download_methods:
        platform = method.__name__.replace("download_", "")
        tried.append(platform)
        input_apk, version = method(app_name, str(cli), str(patches))
        if input_apk:
            logging.info(f"✅ APK obtained from {platform}")
            break

    if input_apk is None:
        # 全ソース失敗 — exit(1) でジョブを赤くする
        logging.error(f"❌ FATAL: Failed to download APK for '{app_name}' from any source")
        logging.error(f"   Tried: {', '.join(tried)}")
        logging.error(f"   Check the per-platform errors above for details.")
        exit(1)

    if input_apk.suffix != ".apk":
        logging.warning("Input file is not .apk, using APKEditor to merge")
        apk_editor = downloader.download_apkeditor()

        merged_apk = input_apk.with_suffix(".apk")

        utils.run_process([
            "java", "-jar", apk_editor, "m",
            "-i", str(input_apk),
            "-o", str(merged_apk)
        ], silent=True)

        input_apk.unlink(missing_ok=True)

        if not merged_apk.exists():
            logging.error("❌ FATAL: Merged APK file not found after APKEditor run")
            exit(1)

        clean_name = re.sub(r'\(\d+\)', '', merged_apk.name)
        clean_name = re.sub(r'-\d+_', '_', clean_name)
        if clean_name != merged_apk.name:
            clean_apk = merged_apk.with_name(clean_name)
            merged_apk.rename(clean_apk)
            merged_apk = clean_apk

        input_apk = merged_apk
        logging.info(f"Merged APK file generated: {input_apk}")

    # ARCHITECTURE PROCESSING
    if arch != "universal":
        logging.info(f"Processing APK for {arch} architecture...")
        if arch == "arm64-v8a":
            utils.run_process([
                "zip", "--delete", str(input_apk),
                "lib/x86/*", "lib/x86_64/*", "lib/armeabi-v7a/*"
            ], silent=True, check=False)
        elif arch == "armeabi-v7a":
            utils.run_process([
                "zip", "--delete", str(input_apk),
                "lib/x86/*", "lib/x86_64/*", "lib/arm64-v8a/*"
            ], silent=True, check=False)
    else:
        utils.run_process([
            "zip", "--delete", str(input_apk),
            "lib/x86/*", "lib/x86_64/*"
        ], silent=True, check=False)

    exclude_patches = []
    include_patches = []

    patches_path = Path("patches") / f"{app_name}-{source}.txt"
    if patches_path.exists():
        with patches_path.open('r') as patches_file:
            for line in patches_file:
                line = line.strip()
                if line.startswith('-'):
                    exclude_patches.extend(["-d", line[1:].strip()])
                elif line.startswith('+'):
                    include_patches.extend(["-e", line[1:].strip()])

    # Repair corrupted APK
    logging.info("Checking APK for corruption...")
    try:
        fixed_apk = Path(f"{app_name}-fixed-v{version}.apk")
        subprocess.run([
            "zip", "-FF", str(input_apk), "--out", str(fixed_apk)
        ], check=False, capture_output=True)
        if fixed_apk.exists() and fixed_apk.stat().st_size > 0:
            input_apk.unlink(missing_ok=True)
            fixed_apk.rename(input_apk)
            logging.info("APK fixed successfully")
    except Exception as e:
        logging.warning(f"Could not fix APK: {e}")

    output_apk = Path(f"{app_name}-{arch}-patch-v{version}.apk")

    if patches.suffix == ".mpp":
        is_morphe = True

    # PATCHING
    if is_morphe:
        logging.info("🔧 Using Morphe patching system...")
        try:
            morphe_cmd = [
                "java", "-jar", str(cli),
                "patch", "--patches", str(patches),
                "--out", str(output_apk), str(input_apk),
                *exclude_patches, *include_patches
            ]
            utils.run_process(morphe_cmd, stream=True)
        except subprocess.CalledProcessError:
            logging.info("Trying alternative Morphe command format...")
            morphe_cmd = [
                "java", "-jar", str(cli),
                "--patches", str(patches),
                "--input", str(input_apk),
                "--output", str(output_apk)
            ]
            utils.run_process(morphe_cmd, stream=True)
    else:
        logging.info("🔧 Using ReVanced patching system...")
        cli_name = Path(cli).name.lower()
        is_revanced_v6_or_newer = any(f'revanced-cli-{v}' in cli_name for v in ['6', '7', '8'])

        if is_revanced_v6_or_newer:
            utils.run_process([
                "java", "-jar", str(cli),
                "patch", "-p", str(patches), "-b",
                "--out", str(output_apk), str(input_apk),
                *exclude_patches, *include_patches
            ], stream=True)
        else:
            utils.run_process([
                "java", "-jar", str(cli),
                "patch", "--patches", str(patches),
                "--out", str(output_apk), str(input_apk),
                *exclude_patches, *include_patches
            ], stream=True)

    input_apk.unlink(missing_ok=True)

    if not output_apk.exists():
        logging.error(f"❌ FATAL: Patched APK not found after patching: {output_apk}")
        logging.error(f"   This means the patch command failed or produced no output.")
        exit(1)

    # SIGNING
    signed_apk = Path(f"{app_name}-{arch}-{name}-v{version}.apk")

    apksigner = utils.find_apksigner()
    if not apksigner:
        logging.error("❌ FATAL: apksigner not found. Cannot sign APK.")
        exit(1)

    signed_ok = False
    try:
        utils.run_process([
            str(apksigner), "sign", "--verbose",
            "--ks", "keystore/public.jks",
            "--ks-pass", "pass:public",
            "--key-pass", "pass:public",
            "--ks-key-alias", "public",
            "--in", str(output_apk), "--out", str(signed_apk)
        ], stream=True)
        signed_ok = True
    except Exception as e:
        logging.warning(f"Standard signing failed: {e}, trying with --min-sdk-version 21")
        try:
            utils.run_process([
                str(apksigner), "sign", "--verbose",
                "--min-sdk-version", "21",
                "--ks", "keystore/public.jks",
                "--ks-pass", "pass:public",
                "--key-pass", "pass:public",
                "--ks-key-alias", "public",
                "--in", str(output_apk), "--out", str(signed_apk)
            ], stream=True)
            signed_ok = True
        except Exception as e2:
            logging.error(f"❌ FATAL: Both signing attempts failed for {app_name}: {e2}")

    output_apk.unlink(missing_ok=True)

    if not signed_ok or not signed_apk.exists():
        logging.error(f"❌ FATAL: Signed APK not produced for {app_name}")
        exit(1)

    print(f"✅ APK built: {signed_apk.name}")
    return str(signed_apk)


def main():
    app_name = getenv("APP_NAME")
    source = getenv("SOURCE")

    if not app_name or not source:
        logging.error("❌ FATAL: APP_NAME and SOURCE environment variables must be set")
        exit(1)

    arches = ["universal"]
    arch_config_path = Path("arch-config.json")
    if arch_config_path.exists():
        with open(arch_config_path) as f:
            arch_config = json.load(f)

        if not isinstance(arch_config, list):
            logging.error(
                "arch-config.json must be a JSON array. "
                "Got %s instead. Falling back to universal build.",
                type(arch_config).__name__,
            )
        else:
            for entry in arch_config:
                if not isinstance(entry, dict):
                    continue
                if entry.get("app_name") == app_name and entry.get("source") == source:
                    arches = entry.get("arches") or entry.get("arch") or arches
                    break
    else:
        logging.warning("arch-config.json not found, building universal only")

    built_apks = []
    failed_arches = []
    for arch in arches:
        logging.info(f"🔨 Building {app_name} for {arch} architecture...")
        try:
            apk_path = run_build(app_name, source, arch)
            if apk_path:
                built_apks.append(apk_path)
                print(f"✅ Built {arch} version: {Path(apk_path).name}")
            else:
                failed_arches.append(arch)
        except SystemExit:
            # run_build が exit(1) した場合はそのまま伝播
            raise

    print(f"\n🎯 Built {len(built_apks)} / {len(arches)} APK(s) for {app_name}:")
    for apk in built_apks:
        print(f"  📱 {Path(apk).name}")

    if failed_arches:
        logging.error(f"❌ Failed architectures for {app_name}: {', '.join(failed_arches)}")
        exit(1)

if __name__ == "__main__":
    main()
