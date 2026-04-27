import json, os, sys, logging, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
logging.basicConfig(level=logging.WARNING)

with open("last-tags.json") as f:
    current = json.load(f)

with open("my-patch-config.json") as f:
    patch_list = json.load(f)["patch_list"]

seen = set()
apps = []
for item in patch_list:
    if item["app_name"] not in seen:
        seen.add(item["app_name"])
        apps.append(item["app_name"])

from src import apkmirror, apkpure, uptodown, aptoide, github as github_mod

platform_order = ["apkmirror", "apkpure", "uptodown", "aptoide", "github"]
mod_map = {"github": github_mod, "apkmirror": apkmirror, "apkpure": apkpure,
           "uptodown": uptodown, "aptoide": aptoide}

for app in apps:
    key = f"apk_{app}"
    for platform in platform_order:
        config_path = pathlib.Path("apps") / platform / f"{app}.json"
        if not config_path.exists():
            continue
        try:
            with open(config_path) as f:
                config = json.load(f)
            ver = mod_map[platform].get_latest_version(app, config)
            if ver:
                current[key] = str(ver)
                break
        except Exception:
            continue

with open("last-tags.json", "w") as f:
    json.dump(current, f, indent=2)
print("APK versions saved to last-tags.json")
