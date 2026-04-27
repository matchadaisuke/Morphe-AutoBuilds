import json, os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

upd = {
    'morphe':          os.environ.get('UPD_MORPHE',  'true'),
    'revanced-anddea': os.environ.get('UPD_ANDDEA',  'true'),
    'piko':            os.environ.get('UPD_PIKO',    'true'),
    'hoo':             os.environ.get('UPD_HOO',     'true'),
    'rookie':          os.environ.get('UPD_ROOKIE',  'true'),
    'tosox':           os.environ.get('UPD_TOSOX',   'true'),
    'yuzu':            os.environ.get('UPD_YUZU',    'true'),
    'dropped':         os.environ.get('UPD_DROPPED', 'true'),
}
all_items = json.load(open('./my-patch-config.json'))['patch_list']
all_true = all(v == 'true' for v in upd.values())
matrix = all_items if all_true else [i for i in all_items if upd.get(i['source']) == 'true']
if not matrix:
    print('WARNING: No sources were updated - matrix is empty.', file=sys.stderr)
with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
    f.write(f"matrix={json.dumps(matrix)}\n")
