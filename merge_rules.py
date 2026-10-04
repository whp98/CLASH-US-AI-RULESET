#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
US-AI Clash 规则集合并工具
扫描 domain/ 目录下的所有公司规则文件，去重并汇总合并生成 US-AI.yaml。
支持作为 Git pre-commit hook 在提交前自动执行。
"""

import os
import sys
import re
import argparse
import stat
from pathlib import Path


def parse_domain_file(filepath: Path):
    """
    解析单个规则文件，提取公司标题和有效 payload 规则列表。
    返回 (company_title, rules)，其中 rules 元素为 (rule_text, comment_text)。
    """
    company_title = filepath.stem
    rules = []

    # 正则提取规则和注释：
    # 例如：- DOMAIN-SUFFIX,chatgpt.com # 网页端主站
    # 或：- 'DOMAIN-SUFFIX,chatgpt.com' # 网页端主站
    rule_pattern = re.compile(
        r'^\s*-\s*[\'"]?([A-Z0-9_-]+,[^\s#\'"]+)[\'"]?\s*(?:#\s*(.*))?$'
    )

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_payload = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 检查首行注释作为公司友好名称
        if stripped.startswith('#') and not in_payload:
            title_candidate = stripped.lstrip('#').strip()
            if title_candidate and not title_candidate.startswith('='):
                company_title = title_candidate
            continue

        if stripped.startswith('payload:'):
            in_payload = True
            continue

        if in_payload:
            m = rule_pattern.match(stripped)
            if m:
                rule_text = m.group(1).strip()
                comment_text = m.group(2).strip() if m.group(2) else ""
                rules.append((rule_text, comment_text))

    return company_title, rules


def merge_rules(domain_dir: Path, output_file: Path, check_only: bool = False):
    """
    合并 domain_dir 目录下的所有规则文件并写入 output_file。
    """
    if not domain_dir.is_dir():
        print(f"[错误] 目录不存在: {domain_dir}", file=sys.stderr)
        return False

    yaml_files = sorted(
        [p for p in domain_dir.iterdir() if p.suffix.lower() in ('.yaml', '.yml')]
    )

    if not yaml_files:
        print(f"[警告] 目录 {domain_dir} 中未找到任何 YAML 规则文件。", file=sys.stderr)
        return False

    seen_rules = set()
    categories = []
    total_rule_count = 0
    duplicate_count = 0

    for file_path in yaml_files:
        company_title, rules = parse_domain_file(file_path)
        valid_rules = []
        for rule_text, comment in rules:
            rule_key = rule_text.upper()
            if rule_key in seen_rules:
                duplicate_count += 1
                continue
            seen_rules.add(rule_key)
            valid_rules.append((rule_text, comment))
            total_rule_count += 1

        if valid_rules:
            categories.append({
                "file": file_path.name,
                "title": company_title,
                "rules": valid_rules
            })

    # 生成目标 YAML 内容
    lines = [
        "# ==============================================================================",
        "# Clash Rule-Set: US-AI (全美主流 AI 公司服务规则集)",
        f"# 总计公司分类: {len(categories)} 个",
        f"# 总计独立规则: {total_rule_count} 条",
        "# 自动生成工具: merge_rules.py",
        "# ==============================================================================",
        "payload:",
    ]

    for cat in categories:
        lines.append("")
        lines.append(f"  # ----------------------------------------------------------------------------")
        lines.append(f"  # [{cat['title']}] ({cat['file']}) - 共 {len(cat['rules'])} 条规则")
        lines.append(f"  # ----------------------------------------------------------------------------")
        for rule_text, comment in cat["rules"]:
            if comment:
                lines.append(f"  - {rule_text} # {comment}")
            else:
                lines.append(f"  - {rule_text}")

    lines.append("")  # 结尾换行
    generated_content = "\n".join(lines)

    if check_only:
        print(f"[检查模式] 发现 {len(categories)} 个分类，{total_rule_count} 条规则，{duplicate_count} 条重复已被过滤。")
        return True

    # 写入目标文件
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(generated_content)

    print(f"[成功] 规则合并完成！已生成 '{output_file}'")
    print(f"       -> 包含公司分类: {len(categories)} 个")
    print(f"       -> 有效独立规则: {total_rule_count} 条")
    if duplicate_count > 0:
        print(f"       -> 过滤重复规则: {duplicate_count} 条")

    return True


def install_git_hook(repo_root: Path):
    """
    在 .git/hooks/ 目录下创建可执行的 pre-commit 钩子。
    """
    git_dir = repo_root / '.git'
    if not git_dir.is_dir():
        print(f"[错误] '{repo_root}' 不是一个 Git 仓库，请先执行 git init。", file=sys.stderr)
        return False

    hooks_dir = git_dir / 'hooks'
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / 'pre-commit'

    hook_script = """#!/bin/sh
# US-AI Clash Ruleset Pre-commit Hook
# 自动合并规则并确保 US-AI.yaml 处于最新状态

echo "[Git Hook] 正在自动合并 US-AI 规则集..."
python3 merge_rules.py

if [ $? -ne 0 ]; then
    echo "[Git Hook 错误] 规则合并失败，中断提交！" >&2
    exit 1
fi

# 将更新后的 US-AI.yaml 添加到待提交暂存区
if [ -f "US-AI.yaml" ]; then
    git add US-AI.yaml
    echo "[Git Hook] 已将最新的 US-AI.yaml 添加到暂存区。"
fi

exit 0
"""

    with open(hook_path, 'w', encoding='utf-8') as f:
        f.write(hook_script)

    # 增加执行权限 chmod +x
    st = os.stat(hook_path)
    os.chmod(hook_path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"[成功] Git pre-commit hook 已成功配置于: {hook_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="US-AI Clash 规则集合并工具")
    parser.add_argument(
        '--domain-dir',
        default='domain',
        help='存放各公司规则文件的目录 (默认: domain)'
    )
    parser.add_argument(
        '--output',
        default='US-AI.yaml',
        help='合并后的输出文件路径 (默认: US-AI.yaml)'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='仅检查规则文件完整性，不写入输出文件'
    )
    parser.add_argument(
        '--install-hook',
        action='store_true',
        help='将合并工具安装为 Git pre-commit 钩子'
    )

    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent

    if args.install_hook:
        success = install_git_hook(repo_root)
        if not success:
            sys.exit(1)

    domain_path = repo_root / args.domain_dir
    output_path = repo_root / args.output

    success = merge_rules(domain_path, output_path, check_only=args.check)
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
