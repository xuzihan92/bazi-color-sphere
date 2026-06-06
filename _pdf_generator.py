#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八字色彩球体理论 - 核心文档PDF生成器
将4份核心理论文档合并转换为PDF存证版本
"""

import markdown
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CORE_DOCS = [
    ("球体模型修正_土轴四行_v2.0.md", "第一部分：土轴四行模型 v2.0"),
    ("跨学科交叉验证_v1_vs_v2.md", "第二部分：跨学科交叉验证"),
    ("后天八卦螺旋球体模型_v3.0.md", "第三部分：后天八卦双螺旋 v3.0"),
    ("v3.0_理论学术论证.md", "第四部分：理论学术论证"),
]

HTML_HEADER = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>八字色彩球体理论 - 核心文档存证版</title>
<style>
@page {
    size: A4;
    margin: 2.5cm 2cm;
    @bottom-center {
        content: counter(page);
        font-size: 10pt;
        color: #666;
    }
}
* { box-sizing: border-box; }
body {
    font-family: "SimSun", "Noto Serif CJK SC", "Source Han Serif SC", serif;
    font-size: 11pt;
    line-height: 1.8;
    color: #333;
    max-width: 21cm;
    margin: 0 auto;
    padding: 2cm;
}
h1 {
    font-size: 20pt;
    text-align: center;
    border-bottom: 3px double #333;
    padding-bottom: 0.5em;
    margin-bottom: 1em;
    page-break-before: always;
}
h1:first-of-type {
    page-break-before: auto;
}
h2 {
    font-size: 15pt;
    border-left: 5px solid #8B4513;
    padding-left: 0.5em;
    margin-top: 1.5em;
    color: #222;
}
h3 {
    font-size: 13pt;
    color: #444;
    margin-top: 1.2em;
}
h4 {
    font-size: 11.5pt;
    color: #555;
}
p { margin: 0.8em 0; text-align: justify; }
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    font-size: 10pt;
}
th, td {
    border: 1px solid #ccc;
    padding: 6px 10px;
    text-align: left;
}
th {
    background: #f5f5f5;
    font-weight: bold;
}
tr:nth-child(even) { background: #fafafa; }
code {
    background: #f4f4f4;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: "Consolas", monospace;
    font-size: 10pt;
}
pre {
    background: #f8f8f8;
    padding: 1em;
    border-radius: 5px;
    overflow-x: auto;
    border-left: 4px solid #8B4513;
    font-size: 9.5pt;
}
pre code { background: none; padding: 0; }
blockquote {
    border-left: 4px solid #8B4513;
    margin: 1em 0;
    padding: 0.5em 1em;
    background: #faf8f5;
    color: #555;
}
ul, ol { margin: 0.5em 0; padding-left: 2em; }
li { margin: 0.3em 0; }
img { max-width: 100%; height: auto; display: block; margin: 1em auto; }
.cover {
    text-align: center;
    padding-top: 8cm;
    page-break-after: always;
}
.cover h1 {
    font-size: 26pt;
    border: none;
    margin-bottom: 2em;
}
.cover .meta {
    font-size: 12pt;
    color: #666;
    line-height: 2.2;
}
.cover .seal {
    margin-top: 4em;
    border: 2px solid #8B4513;
    display: inline-block;
    padding: 1em 2em;
    color: #8B4513;
    font-weight: bold;
}
hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 2em 0;
}
.toc { page-break-after: always; }
.toc h2 { border-left: none; text-align: center; }
.toc ul { list-style: none; padding-left: 0; }
.toc li { margin: 0.6em 0; padding-left: 1em; border-left: 3px solid #ddd; }
.toc .part { font-weight: bold; color: #8B4513; }
</style>
</head>
<body>
"""

COVER_PAGE = """
<div class="cover">
    <h1>八字色彩球体理论</h1>
    <div class="meta">
        <p><strong>核心文档存证版</strong></p>
        <p>理论创始人：梓涵</p>
        <p>协作团队：行知阁</p>
        <p>归档时间：{timestamp}</p>
        <p>文档版本：v3.0</p>
        <p>理论演进：v0.1 → v1.0 → v2.0 → v3.0</p>
    </div>
    <div class="seal">
        行知阁 · 原创存证
    </div>
</div>
"""

TOC = """
<div class="toc">
    <h2>目 录</h2>
    <ul>
        <li class="part">第一部分：土轴四行模型 v2.0</li>
        <li class="part">第二部分：跨学科交叉验证</li>
        <li class="part">第三部分：后天八卦双螺旋 v3.0</li>
        <li class="part">第四部分：理论学术论证</li>
    </ul>
    <hr>
    <p style="font-size: 10pt; color: #888; text-align: center;">
        本文件由 Git 提交 {git_commit} 于 {timestamp} 生成<br>
        SHA-256 校验请参见《完整归档存证清单》
    </p>
</div>
"""

HTML_FOOTER = """
<hr>
<div style="text-align: center; font-size: 10pt; color: #888; margin-top: 3em; padding: 2em; background: #fafafa;">
    <p><strong>八字色彩球体理论 · 核心文档存证版</strong></p>
    <p>理论创始人：梓涵 | 协作团队：行知阁</p>
    <p>生成时间：{timestamp}</p>
    <p>本文档仅供学术研究与原创存证使用</p>
</div>
</body>
</html>
"""


def generate_pdf():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git_commit = "13fb1c4"  # root commit hash

    html_parts = [HTML_HEADER]
    html_parts.append(COVER_PAGE.format(timestamp=timestamp))
    html_parts.append(TOC.format(git_commit=git_commit, timestamp=timestamp))

    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc'])

    for filename, part_title in CORE_DOCS:
        filepath = os.path.join(BASE_DIR, filename)
        if not os.path.exists(filepath):
            print(f"警告：找不到文件 {filename}", file=sys.stderr)
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 移除HTML注释水印
        import re
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

        # 重置markdown解析器
        md.reset()
        html_body = md.convert(content)

        html_parts.append(f'<h1>{part_title}</h1>\n')
        html_parts.append(html_body)
        html_parts.append('<hr>\n')

    html_parts.append(HTML_FOOTER.format(timestamp=timestamp))

    output_html = os.path.join(BASE_DIR, '_core_docs_for_pdf.html')
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))

    print(f"HTML已生成: {output_html}")
    return output_html


if __name__ == '__main__':
    generate_pdf()
