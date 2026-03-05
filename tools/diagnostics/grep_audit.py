import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'tools' / 'diagnostics' / 'grep_audit.txt'
cmd = [
    'rg',
    '-n',
    "Window\\.size|Config\\.set\\('graphics'|C:\\\\|D:\\\\|winsound|winreg|ctypes\\.windll|pyjnius|android\\.permissions|materialyoucolor|filetype|orientation|landscape|AndroidManifest\\.xml",
    '.',
]
proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
content = []
content.append('COMMAND: ' + ' '.join(cmd))
content.append('EXIT: ' + str(proc.returncode))
content.append('STDOUT:')
content.append(proc.stdout)
content.append('STDERR:')
content.append(proc.stderr)
OUT.write_text('\n'.join(content), encoding='utf-8')
print(f'Wrote {OUT}')
