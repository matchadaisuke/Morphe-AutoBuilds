import json, os, sys, pathlib, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

reuse_json = os.environ.get("REUSE_JSON", "{}")
if not reuse_json or reuse_json == "{}":
    print("No APKs to reuse.")
    sys.exit(0)

data = json.loads(reuse_json)
token = os.environ.get("GITHUB_TOKEN", "")
os.makedirs("./release-apks", exist_ok=True)

for source, url in data.items():
    fname = url.split('/')[-1]
    print(f"Downloading reused APK for {source}: {url}")
    subprocess.run([
        'curl', '-sL',
        '-H', f'Authorization: token {token}',
        url, '-o', f'./release-apks/{fname}'
    ], check=False)
