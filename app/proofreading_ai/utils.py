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
    校正結果をハイライト付きHTMLとして生成する（4色カテゴリー対応・改良版）
    original_text: 元のテキスト（HTMLタグ含む）
    corrections: [{'original': 'xxx', 'corrected': 'yyy', 'reason': '...', 'category': 'tone|typo|dict|inconsistency'}]
    """
    if not corrections:
        # 修正箇所がない場合は元のテキストをエスケープして返す
        return html.escape(original_text)
    
    result = []
    last_idx = 0
    used_positions = set()  # 使用済み位置を記録
    
    # 修正箇所を位置順にソート
    sorted_corrections = []
    for corr in corrections:
        original_word = corr.get("original", "")
        if original_word:
            # 複数の出現位置を検索
            start = 0
            while True:
                pos = original_text.find(original_word, start)
                if pos == -1:
                    break
                # 既に使用済みでない位置のみ追加
                if pos not in used_positions:
                    sorted_corrections.append((pos, corr))
                    break
                start = pos + 1
    
    # 位置順にソート
    sorted_corrections.sort(key=lambda x: x[0])
    
    for start_pos, corr in sorted_corrections:
        # 既に処理済みの位置はスキップ
        if start_pos in used_positions:
            continue
            
        # 現在の位置より前の位置はスキップ
        if start_pos < last_idx:
            continue
            
        original_word = corr.get("original", "")
        corrected_word = corr.get("corrected", "")
        reason = corr.get("reason", "")
        category = corr.get("category", "general")
        
        end_pos = start_pos + len(original_word)
        
        # 修正前の部分
        result.append(html.escape(original_text[last_idx:start_pos]))
        
        # カテゴリーに応じたCSSクラスを決定
        css_class = f"correction-{category}" if category in ["tone", "typo", "dict", "inconsistency"] else "correction-text"
        
        # カテゴリー名とアイコンのマッピング
        category_info = {
            'typo': {'name': '誤字修正', 'icon': '🔤', 'color': '#dc2626'},
            'tone': {'name': '言い回し改善', 'icon': '✨', 'color': '#7c3aed'},
            'dict': {'name': '辞書ルール', 'icon': '📚', 'color': '#d97706'},
            'inconsistency': {'name': '矛盾チェック', 'icon': '⚠️', 'color': '#c2410c'}
        }
        
        cat_info = category_info.get(category, {'name': '修正', 'icon': '📝', 'color': '#6b7280'})
        
        # 修正箇所をハイライト（4色カテゴリー対応・修正前文字列表示に変更）
        result.append(
            f'<span class="correction-span" '
            f'data-original="{html.escape(original_word)}" '
            f'data-corrected="{html.escape(corrected_word)}" '
            f'data-reason="{html.escape(reason)}" '
            f'data-category="{category}">'
            f'<span class="{css_class}">{html.escape(original_word)}</span>'
            f'<span class="correction-tooltip">'
            f'<div class="tooltip-category-badge" style="background: {cat_info["color"]}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-bottom: 8px; text-align: center;">'
            f'{cat_info["icon"]} {cat_info["name"]}'
            f'</div>'
            f'<div class="tooltip-original clickable-correction" data-action="revert" title="クリックして元に戻す">{html.escape(original_word)}</div>'
            f'<div class="tooltip-corrected clickable-correction" data-action="apply" title="クリックして修正を適用">{html.escape(corrected_word)}</div>'
            f'<div class="tooltip-reason">{html.escape(reason)}</div>'
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
    Claude Sonnet 4の校正API返却値から修正箇所リストをパースする（4色カテゴリー対応）
    - カテゴリー: tone | (変更前) -> (変更後): 理由
    の形式を抽出し、original, corrected, reason, categoryのdictリストで返す
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
        
        # Claude Sonnet 4の新形式: - カテゴリー: tone | (変更前) -> (変更後): 理由
        category_match = re.match(r"- カテゴリー: (tone|typo|dict|inconsistency) \| \((.*?)\) -> \((.*?)\): ?(.*)", line)
        if category_match:
            category, original, corrected, reason = category_match.groups()
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
                    "category": category,
                })
            continue
        
        # 従来形式（後方互換性のため）: - 行番号: (変更前) -> (変更後): 理由
        legacy_match = re.match(r"- [^:]+: \((.*?)\) -> \((.*?)\): ?(.*)", line)
        if legacy_match:
            original, corrected, reason = legacy_match.groups()
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
                    "category": "general",  # デフォルトカテゴリー
                })
    
    return corrections 