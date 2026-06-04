#!/usr/bin/env python3
"""Build IndustryViewer.html from template files + background PNG.

Reads:
  - IndustryViewer_Template.html  (HTML skeleton with <!--INJECT_CSS--> and <!--INJECT_JS-->)
  - IndustryViewer_Template.css   (all styles, injected into <!--INJECT_CSS-->)
  - IndustryViewer_Template.js    (all logic, injected into <!--INJECT_JS-->)
  - background.png                (background image, base64-encoded)

Writes:
  - IndustryViewer.html           (final self-contained single file)
"""

import os
import sys
import base64

VERSION = "1.1"
BASE = os.path.dirname(os.path.abspath(__file__))


def read_file(filename):
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        print(f'ERROR: Missing file: {filename}', file=sys.stderr)
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def read_binary(filename):
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        print(f'ERROR: Missing file: {filename}', file=sys.stderr)
        sys.exit(1)
    with open(path, 'rb') as f:
        return f.read()


def main():
    # 1. Read HTML skeleton
    html = read_file('IndustryViewer_Template.html')

    # 2. Read CSS template → inject
    css = read_file('IndustryViewer_Template.css')
    if '<!--INJECT_CSS-->' not in html:
        print('ERROR: Missing <!--INJECT_CSS--> placeholder in HTML template', file=sys.stderr)
        sys.exit(1)
    html = html.replace('<!--INJECT_CSS-->', f'\n{css}\n  ')

    # 3. Read JS template → inject
    js = read_file('IndustryViewer_Template.js')
    if '<!--INJECT_JS-->' not in html:
        print('ERROR: Missing <!--INJECT_JS--> placeholder in HTML template', file=sys.stderr)
        sys.exit(1)
    html = html.replace('<!--INJECT_JS-->', f'\n{js}\n  ')

    # 4. Inject version into JS (console.log)
    html = html.replace('/*INJECT_VERSION*/', f'"{VERSION}"')

    # 5. Inject base64 PNG
    png_data = read_binary('background.png')
    b64 = base64.b64encode(png_data).decode()
    html = html.replace(
        'BG64_PLACEHOLDER_WILL_BE_REPLACED_BY_SCRIPT',
        f'url("data:image/png;base64,{b64}")'
    )

    # 6. Inject version HTML comment
    html = html.replace('</head>', f'  <!-- IndustryViewer v{VERSION} -->\n</head>')

    # 7. Write output
    final_path = os.path.join(BASE, 'IndustryViewer.html')
    with open(final_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # Verification
    passed = True
    checks = {
        '<!--INJECT_CSS-->': 'UNRESOLVED: <!--INJECT_CSS--> still present',
        '<!--INJECT_JS-->': 'UNRESOLVED: <!--INJECT_JS--> still present',
        'BG64_PLACEHOLDER_WILL_BE_REPLACED_BY_SCRIPT': 'UNRESOLVED: BG64 placeholder still present',
    }
    for token, msg in checks.items():
        if token in html:
            print(f'  FAIL: {msg}', file=sys.stderr)
            passed = False

    print(f'Version: v{VERSION}')
    print(f'Output: {len(html)} bytes')
    print(f'  base64 injected: {"data:image/png;base64," in html}')
    print(f'  radial-gradient: {html.count("radial-gradient")}')
    print(f'  mousemove: {html.count("mousemove")}')
    print(f'  saveApiKey: {html.count("saveApiKey")}')
    print(f'  clearApiKey: {html.count("clearApiKey")}')
    print(f'  loadSavedApiKey: {html.count("loadSavedApiKey")}')
    print(f'  INJECT_CSS resolved: {"<!--INJECT_CSS-->" not in html}')
    print(f'  INJECT_JS resolved: {"<!--INJECT_JS-->" not in html}')
    print(f'  version injected: {"<!-- IndustryViewer v" in html}')

    if passed:
        print('BUILD COMPLETE')
    else:
        print('BUILD FAILED', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()