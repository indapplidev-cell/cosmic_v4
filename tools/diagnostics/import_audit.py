import ast
import json
from pathlib import Path

EXCLUDE_DIRS = {'.git', '.venv', 'venv', 'build', 'bin', 'dist', '__pycache__', '.buildozer'}
ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / 'tools' / 'diagnostics' / 'imports.json'
OUT_MD = ROOT / 'tools' / 'diagnostics' / 'imports.md'

modules = {}

def add_module(mod, file_path):
    if not mod:
        return
    top = mod.split('.')[0]
    rec = modules.setdefault(top, {'count': 0, 'files': set()})
    rec['count'] += 1
    rec['files'].add(str(file_path.relative_to(ROOT)).replace('\\\\', '/'))

for path in ROOT.rglob('*.py'):
    rel_parts = set(path.relative_to(ROOT).parts)
    if rel_parts & EXCLUDE_DIRS:
        continue
    try:
        src = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            src = path.read_text(encoding='utf-8-sig')
        except Exception:
            continue
    except Exception:
        continue
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                add_module(alias.name, path)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                add_module(node.module, path)

json_data = []
for mod, data in sorted(modules.items()):
    files = sorted(data['files'])
    json_data.append({'module': mod, 'count': data['count'], 'files': files})

OUT_JSON.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding='utf-8')

lines = [
    '| module | count | example files |',
    '|---|---:|---|',
]
for item in json_data:
    examples = ', '.join(item['files'][:3])
    lines.append(f"| {item['module']} | {item['count']} | {examples} |")
OUT_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(f'Wrote {OUT_JSON}')
print(f'Wrote {OUT_MD}')
