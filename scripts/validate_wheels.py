#!/usr/bin/env python3
"""
Validate wheel ZIP structure and detect issues.
This script mimics the CI validation logic for local testing.
"""

import sys
import zipfile
from pathlib import Path


def validate_wheel(wheel_path: Path) -> tuple[bool, list[str]]:
    """Validate wheel ZIP structure and detect issues."""
    issues = []

    try:
        # Test ZIP integrity
        with zipfile.ZipFile(wheel_path, 'r') as zf:
            bad_file = zf.testzip()
            if bad_file:
                issues.append(f'Corrupt file in ZIP: {bad_file}')

        # Check for trailing data
        with open(wheel_path, 'rb') as f:
            data = f.read()

        # Find End of Central Directory signature
        eocd_sig = b'PK\x05\x06'
        pos = data.rfind(eocd_sig)

        if pos == -1:
            issues.append('No EOCD signature found')
        else:
            # Calculate expected end position
            comment_len = int.from_bytes(data[pos + 20 : pos + 22], 'little')
            eocd_end = pos + 22 + comment_len
            trailing_bytes = len(data) - eocd_end

            if trailing_bytes > 0:
                issues.append(f'Trailing data after EOCD: {trailing_bytes} bytes')

        if issues:
            return False, issues
        return True, []

    except Exception as e:
        return False, [f'Exception during validation: {e}']


def main():
    # Find all wheels in dist/
    dist_dir = Path('dist')
    if not dist_dir.exists():
        print('❌ dist/ directory not found')
        print("Run 'maturin build' first to create wheels")
        return 1

    wheels = list(dist_dir.glob('*.whl'))
    if not wheels:
        print('❌ No wheels found in dist/')
        print("Run 'maturin build' first to create wheels")
        return 1

    print(f'Validating {len(wheels)} wheel(s)...')
    print()

    all_valid = True
    for wheel in sorted(wheels):
        valid, issues = validate_wheel(wheel)
        if valid:
            print(f'✅ {wheel.name}')
        else:
            print(f'❌ {wheel.name}')
            for issue in issues:
                print(f'   - {issue}')
            all_valid = False

    print()
    if not all_valid:
        print('❌ Wheel validation FAILED')
        print()
        print('Wheels have structural issues that would cause PyPI upload to fail.')
        print('This is a bug in the wheel building process.')
        return 1

    print('✅ All wheels passed validation')
    return 0


if __name__ == '__main__':
    sys.exit(main())
