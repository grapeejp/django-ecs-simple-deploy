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


def protect_html_tags(text: str) -> Tuple[str, Dict[str, str]]:
    """
    HTMLタグを一時的に置換してAI処理から保護する
    
    Args:
        text: 元テキスト
        
    Returns:
        タグを置換したテキストとプレースホルダーマッピング辞書
    """
    # HTMLタグを検出する正規表現（コメントタグも含む）
    tag_pattern = r'(<[^>]+>|<!--[\s\S]*?-->)'
    tags = re.findall(tag_pattern, text)
    
    # プレースホルダーとタグのマッピング辞書
    placeholders = {}
    protected_text = text
    
    # 各タグをプレースホルダーに置換
    for i, tag in enumerate(tags):
        placeholder = f"__HTML_TAG_{i}__"
        # 一度に1つだけ置換して、同じタグが複数ある場合でも区別できるようにする
        protected_text = protected_text.replace(tag, placeholder, 1)
        placeholders[placeholder] = tag
    
    return protected_text, placeholders


def restore_html_tags(text: str, placeholders: Dict[str, str]) -> str:
    """
    保護したHTMLタグを元に戻す
    
    Args:
        text: プレースホルダーを含むテキスト
        placeholders: プレースホルダーとタグのマッピング辞書
        
    Returns:
        タグを復元したテキスト
    """
    # 長いプレースホルダーから短いものへと処理するとエラーが少ない
    sorted_placeholders = sorted(placeholders.items(), key=lambda x: len(x[0]), reverse=True)
    
    result = text
    for placeholder, tag in sorted_placeholders:
        # すべてのプレースホルダーを対応するタグに置換
        result = result.replace(placeholder, tag)
    
    return result 


def format_corrections(original_text: str, corrections: List[Dict]) -> str:
    """
    校正結果をハイライト付きHTMLとして生成する
    original_text: 元のテキスト（HTMLタグ含む）
    corrections: [{'original': 'xxx', 'corrected': 'yyy', 'reason': '...'}]
    """
    if not corrections:
        return html.escape(original_text)
    
    result = []
    last_idx = 0
    used_positions = set()  # 使用済み位置を記録
    
    # 修正箇所を位置順にソート
    sorted_corrections = []
    for corr in corrections:
        start = original_text.find(corr["original"])
        if start != -1:
            sorted_corrections.append((start, corr))
    
    # 位置順にソート
    sorted_corrections.sort(key=lambda x: x[0])
    
    for start_pos, corr in sorted_corrections:
        # 既に処理済みの位置はスキップ
        if start_pos in used_positions:
            continue
            
        # 現在の位置より前の位置はスキップ
        if start_pos < last_idx:
            continue
            
        end_pos = start_pos + len(corr["original"])
        
        # 修正前の部分
        result.append(html.escape(original_text[last_idx:start_pos]))
        
        # 修正箇所をハイライト
        result.append(
            f'<span class="correction-span">'
            f'<span class="correction-text">{html.escape(corr["original"])}</span>'
            f'<span class="correction-tooltip">'
            f'<span class="original-text">{html.escape(corr["original"])}</span><br>'
            f'<span class="corrected-text">{html.escape(corr["corrected"])}</span><br>'
            f'<span class="reason-text">{html.escape(corr["reason"])}</span>'
            f'</span>'
            f'</span>'
        )
        
        # 使用済み位置を記録
        for i in range(start_pos, end_pos):
            used_positions.add(i)
            
        last_idx = end_pos
    
    # 残りの部分
    result.append(html.escape(original_text[last_idx:]))
    return ''.join(result)


def parse_corrections_from_text(corrected_text: str) -> List[Dict[str, str]]:
    """
    Claudeの校正API返却値から修正箇所リストをパースする
    - 行番号: (変更前) -> (変更後): 理由
    の形式を抽出し、original, corrected, reasonのdictリストで返す
    """
    corrections = []
    seen_corrections = set()  # 重複チェック用
    
    # 「✅修正箇所：」以降を抽出
    if "✅修正箇所：" not in corrected_text:
        return corrections
    try:
        _, after = corrected_text.split("✅修正箇所：", 1)
    except ValueError:
        return corrections
    
    # 各行をパース
    for line in after.splitlines():
        line = line.strip()
        if not line or not line.startswith("-"):
            continue
        # 例: - 1行目: (増加期傾向) -> (増加傾向): 「増加期傾向」は誤字であり、正しくは「増加傾向」です。
        m = re.match(r"- [^:]+: \((.*?)\) -> \((.*?)\): ?(.*)", line)
        if m:
            original, corrected, reason = m.groups()
            original = original.strip()
            corrected = corrected.strip()
            reason = reason.strip()
            
            # 重複チェック（同じ original -> corrected の組み合わせは除外）
            correction_key = (original, corrected)
            if correction_key not in seen_corrections:
                seen_corrections.add(correction_key)
                corrections.append({
                    "original": original,
                    "corrected": corrected,
                    "reason": reason,
                })
    
    return corrections 