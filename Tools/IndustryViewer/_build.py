#!/usr/bin/env python3
"""Build IndustryViewer.html from IndustryViewer_Template.html + background PNG."""

import os
import base64

BASE = os.path.dirname(os.path.abspath(__file__))

# Read template
template_path = os.path.join(BASE, 'IndustryViewer_Template.html')
with open(template_path, 'r', encoding='utf-8') as f:
    html = f.read()

# === Light mode: make all card/surface backgrounds semi-transparent ===
html = html.replace(
    'background: rgba(255,255,255,0.82);',
    'background: radial-gradient(circle 160px at var(--mx, 50%) var(--my, 50%), transparent 0%, rgba(255,255,255,0.78) 70%);'
)
html = html.replace(
    'background: #fff;\n      padding: 20px 24px;',
    'background: rgba(255,255,255,0.85);\n      padding: 20px 24px;'
)
html = html.replace(
    'background: #fff; padding: 24px; border-radius: 8px;\n      box-shadow: 0 1px 4px rgba(0,0,0,0.08); overflow-x: auto;',
    'background: rgba(255,255,255,0.85); padding: 24px; border-radius: 8px;\n      box-shadow: 0 1px 4px rgba(0,0,0,0.08); overflow-x: auto;'
)
html = html.replace(
    'background: #fafafa; border-bottom: 2px solid #f0f0f0;',
    'background: rgba(250,250,250,0.78); border-bottom: 2px solid #f0f0f0;'
)
html = html.replace(
    'transition: border-color 0.2s; background: #fff; color: #333;',
    'transition: border-color 0.2s; background: rgba(255,255,255,0.85); color: #333;'
)
html = html.replace(
    'border: 1px solid #d9d9d9; background: #fff; border-radius: 4px;\n      padding: 5px 10px; cursor: pointer; color: #333;\n      min-height: 32px;',
    'border: 1px solid #d9d9d9; background: rgba(255,255,255,0.75); border-radius: 4px;\n      padding: 5px 10px; cursor: pointer; color: #333;\n      min-height: 32px;'
)
html = html.replace(
    'min-height: 32px; background: #fff; color: #333;\n    }\n    .pagination .info',
    'min-height: 32px; background: rgba(255,255,255,0.75); color: #333;\n    }\n    .pagination .info'
)
html = html.replace(
    'background: #e6f7ff;\n      border: 1px solid #91d5ff;',
    'background: rgba(230,247,255,0.80);\n      border: 1px solid #91d5ff;'
)
html = html.replace(
    'background: #fffbe6; border: 1px solid #ffe58f;',
    'background: rgba(255,251,230,0.85); border: 1px solid #ffe58f;'
)
html = html.replace(
    'background: #fff; border-radius: 8px; width: 96%; max-width: 1300px;\n      max-height: 94vh;',
    'background: rgba(255,255,255,0.90); border-radius: 8px; width: 96%; max-width: 1300px;\n      max-height: 94vh;'
)

# === Dark mode: semi-transparent ===
html = html.replace(
    'body::before { background: rgba(0,0,0,0.65); }',
    'body::before { background: radial-gradient(circle 160px at var(--mx, 50%) var(--my, 50%), transparent 0%, rgba(0,0,0,0.62) 70%); }'
)
html = html.replace(
    'background: #16213e;\n        box-shadow: 0 1px 4px rgba(0,0,0,0.3);',
    'background: rgba(22,33,62,0.80);\n        box-shadow: 0 1px 4px rgba(0,0,0,0.3);'
)
html = html.replace(
    'background: #1a1a3e; border-bottom-color: #2a2a4e; color: #ccc;',
    'background: rgba(26,26,62,0.78); border-bottom-color: #2a2a4e; color: #ccc;'
)
html = html.replace(
    'background: #1a1a3e; border-color: #3a3a5e; color: #ccc;',
    'background: rgba(26,26,62,0.73); border-color: #3a3a5e; color: #ccc;'
)
html = html.replace(
    'background: #1a1a3e; color: #ddd; border-color: #3a3a5e;',
    'background: rgba(26,26,62,0.73); color: #ddd; border-color: #3a3a5e;'
)
html = html.replace(
    'background: #1a1a3e; color: #ccc; border-color: #3a3a5e; }',
    'background: rgba(26,26,62,0.73); color: #ccc; border-color: #3a3a5e; }'
)
html = html.replace(
    '#search-bar input { background: #1a1a3e;',
    '#search-bar input { background: rgba(26,26,62,0.73);'
)

# === Add mouse spotlight JS ===
old_js = '''    // Enter 键触发查询
    document.addEventListener("DOMContentLoaded", () => {
      initIndustrySelect();
      document.getElementById("apikey-input").addEventListener("keydown", (e) => {
        if (e.key === "Enter") doQuery();
      });
    });'''

new_js = '''    // 鼠标探照灯效果
    document.addEventListener("mousemove", (e) => {
      const mx = (e.clientX / window.innerWidth) * 100;
      const my = (e.clientY / window.innerHeight) * 100;
      document.body.style.setProperty("--mx", mx + "%");
      document.body.style.setProperty("--my", my + "%");
    });
    document.addEventListener("mouseleave", () => {
      document.body.style.setProperty("--mx", "50%");
      document.body.style.setProperty("--my", "50%");
    });
    document.body.style.setProperty("--mx", "50%");
    document.body.style.setProperty("--my", "50%");

    // Enter 键触发查询
    document.addEventListener("DOMContentLoaded", () => {
      initIndustrySelect();
      document.getElementById("apikey-input").addEventListener("keydown", (e) => {
        if (e.key === "Enter") doQuery();
      });
    });'''

html = html.replace(old_js, new_js)

# === Clean up REPLACE artifacts ===
html = html.replace('REPLACE', 'REPLACE')
# Only remove standalone REPLACE on its own line
import re
html = re.sub(r'\nREPLACE\n', '\n', html)

# === Save updated template ===
with open(template_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Template saved: {len(html)} bytes')

# === Inject base64 PNG ===
png_path = os.path.join(BASE, '1290px-BelfastBluray.png')
with open(png_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

html = html.replace(
    'BG64_PLACEHOLDER_WILL_BE_REPLACED_BY_SCRIPT',
    f'url("data:image/png;base64,{b64}")'
)

final_path = os.path.join(BASE, 'IndustryViewer.html')
with open(final_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Final saved: {len(html)} bytes')
print(f'base64: {"data:image/png;base64," in html}')
print(f'radial-gradient: {html.count("radial-gradient")}')
print(f'mousemove: {html.count("mousemove")}')
print(f'rgba(255,255,255,0.85): {html.count("rgba(255,255,255,0.85)")}')
print(f'REPLACE: {html.count("REPLACE")}')
print('BUILD COMPLETE')