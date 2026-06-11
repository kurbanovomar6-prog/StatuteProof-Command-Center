#!/usr/bin/env python3
"""Package the StatuteProof Command Center workspace for sharing or backup.

Creates a zip archive excluding secrets, reference clones, and backup folders.
Usage: python3 tools/package_workspace.py [--output /path/to/output.zip]
"""
import argparse
import sys
import zipfile
from datetime import datetime
from pathlib import Path

EXCLUDE_PATTERNS = {
    '.reference_tmp',
    'node_modules',
    '__pycache__',
    '.DS_Store',
    'planning-reports',
    '.env',
}

EXCLUDE_SUFFIXES = {'.pyc', '.pyo', '.zip'}

EXCLUDE_NAME_PATTERNS = ['_BACKUP_', '.env.']


def should_exclude(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = rel.parts

    for part in parts:
        if part in EXCLUDE_PATTERNS:
            return True
        for pat in EXCLUDE_NAME_PATTERNS:
            if pat in part:
                return True

    if path.suffix in EXCLUDE_SUFFIXES:
        return True

    return False


def main():
    parser = argparse.ArgumentParser(description='Package StatuteProof Command Center')
    parser.add_argument('--output', help='Output zip path', default=None)
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    default_output = root.parent / f'StatuteProof-Command-Center_{timestamp}.zip'
    output_path = Path(args.output) if args.output else default_output

    # Run validation first
    import subprocess
    result = subprocess.run(
        [sys.executable, str(root / 'tools' / 'validate_workspace.py')],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print('Packaging aborted — workspace validation failed.')
        print(result.stderr)
        sys.exit(1)

    files_added = []
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(root.rglob('*')):
            if not path.is_file():
                continue
            if should_exclude(path, root):
                continue
            arcname = path.relative_to(root.parent)
            zf.write(path, arcname)
            files_added.append(str(arcname))

    print(f'\nPackaged {len(files_added)} files → {output_path}')
    print(f'Size: {output_path.stat().st_size / 1024:.1f} KB')


if __name__ == '__main__':
    main()
