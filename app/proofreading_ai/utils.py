import re
import html
import difflib
from typing import Dict, List, Tuple, Union


def get_html_diff(original: str, corrected: str) -> str:
    """
    原文と校正文の差分をHTML形式で返す
    
    Args:
        original: 原文
        corrected: 校正文
        
    Returns:
        差分を表示するHTML
    """
    # HTMLタグのエスケープ（実際の表示用）
    escaped_original = html.escape(original)
    escaped_corrected = html.escape(corrected)
    
    # 差分オブジェクトの生成
    differ = difflib.Differ()
    diff = list(differ.compare(escaped_original.splitlines(), escaped_corrected.splitlines()))
    
    # HTML生成
    html_diff = []
    for line in diff:
        if line.startswith('+ '):
            # 追加行
            html_diff.append(f'<div class="diff-added">{line[2:]}</div>')
        elif line.startswith('- '):
            # 削除行
            html_diff.append(f'<div class="diff-removed">{line[2:]}</div>')
        elif line.startswith('? '):
            # 変更箇所のマーカー（表示しない）
            continue
        else:
            # 変更なし
            html_diff.append(f'<div class="diff-unchanged">{line[2:]}</div>')
    
    return ''.join(html_diff)


def load_replacement_dict(replacements: List[Dict[str, str]]) -> Dict[str, str]:
    """
    置換辞書データをフォーマットする
    
    Args:
        replacements: DBから取得した置換辞書エントリのリスト
        
    Returns:
        {元の語句: 置換後の語句} の形式の辞書
    """
    return {item['original_word']: item['replacement_word'] for item in replacements if item.get('is_active', True)}


def protect_html_tags(text: str) -> Tuple[str, List[Tuple[str, str]]]:
    """
    HTMLタグを一時的に置換してAI処理から保護する
    
    Args:
        text: 元テキスト
        
    Returns:
        タグを置換したテキストとプレースホルダー情報のリスト
    """
    tag_pattern = r'(<[^>]+>)'
    tags = re.findall(tag_pattern, text)
    placeholders = []
    
    # 各タグをプレースホルダーに置換
    for i, tag in enumerate(tags):
        placeholder = f"__TAG_{i}__"
        text = text.replace(tag, placeholder, 1)
        placeholders.append((placeholder, tag))
    
    return text, placeholders


def restore_html_tags(text: str, placeholders: List[Tuple[str, str]]) -> str:
    """
    保護したHTMLタグを元に戻す
    
    Args:
        text: プレースホルダーを含むテキスト
        placeholders: プレースホルダーとタグのペアのリスト
        
    Returns:
        タグを復元したテキスト
    """
    for placeholder, tag in placeholders:
        text = text.replace(placeholder, tag)
    return text 