import json
import time
from typing import Dict, Any, Tuple, List
import random
import logging
import re
import html

from ..utils import protect_html_tags, restore_html_tags

logger = logging.getLogger(__name__)

class MockBedrockClient:
    """
    BedrockClientのモッククラス（テスト用）
    実際のAWS Bedrockを呼び出さずにテスト可能
    """
    
    def __init__(self):
        """
        モッククライアントの初期化
        """
        self.input_price_per_1k_tokens = 0.003
        self.output_price_per_1k_tokens = 0.015
        self.yen_per_dollar = 150
    
    def count_tokens(self, text: str) -> int:
        """
        トークン数を概算する簡易的な方法
        
        Args:
            text: トークン数を計算するテキスト
            
        Returns:
            概算トークン数
        """
        return int(len(text) * 1.5)
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        コストを計算する
        
        Args:
            input_tokens: 入力トークン数
            output_tokens: 出力トークン数
            
        Returns:
            日本円でのコスト
        """
        input_cost = (input_tokens / 1000) * self.input_price_per_1k_tokens
        output_cost = (output_tokens / 1000) * self.output_price_per_1k_tokens
        return (input_cost + output_cost) * self.yen_per_dollar
    
    def format_corrections(self, corrections: List[str]) -> str:
        """
        修正項目のリストをフォーマットする
        
        Args:
            corrections: 修正項目のリスト
            
        Returns:
            フォーマットされた修正テキスト
        """
        if not corrections:
            return "✅修正箇所：\n修正箇所はありませんでした。"
        
        return "✅修正箇所：\n" + "\n".join(corrections)
    
    def proofread_text(self, text: str, replacement_dict: Dict[str, str] = None) -> Tuple[str, str, float, Dict]:
        """
        テキストを校正する（モック版）
        
        Args:
            text: 校正する原文
            replacement_dict: 置換辞書
            
        Returns:
            校正されたテキスト、修正箇所の説明、処理時間、コスト情報のタプル
        """
        # 処理時間をシミュレート
        start_time = time.time()
        # テキストの長さに応じて待機（実際のAPIコールをシミュレート）
        wait_time = min(3 + len(text) / 5000, 10)
        time.sleep(wait_time)
        
        # HTMLタグをエスケープしてテキストとして扱えるようにする
        text_with_escaped_tags = html.escape(text, quote=True)  # HTMLタグをエスケープ（"<" を "&lt;" に変換、引用符もエスケープ）
        
        # 置換辞書を適用
        corrected_text = text_with_escaped_tags
        corrections = []
        highlight_replacements = []  # ハイライト用の置換情報を保存するリスト
        
        # 特定の文章に対する具体的な修正を追加（テスト用）
        if "&lt;div class=&quot;comment&quot;&gt;" in corrected_text:
            original = "&lt;div class=&quot;comment&quot;&gt;"
            replacement = "&lt;div class=&quot;comment&quot;&gt;"  # 変更なし
            highlight_replacements.append((original, replacement, "HTMLタグは修正しません"))
            corrections.append(f"- 1行目: ({original}) -> ({replacement}): HTMLタグは修正しません")
        
        if "２０２４年" in corrected_text:
            original = "２０２４年"
            replacement = "2024年"
            highlight_replacements.append((original, replacement, "数字の表記を半角に統一"))
            corrections.append(f"- 3行目: ({original}) -> ({replacement}): 数字の表記を半角に統一")
        
        if "いわれる" in corrected_text:
            original = "いわれる"
            replacement = "言われる"
            highlight_replacements.append((original, replacement, "ひらがなを漢字に修正"))
            corrections.append(f"- 3行目: ({original}) -> ({replacement}): ひらがなを漢字に修正")
        
        if "こどもたち" in corrected_text:
            original = "こどもたち"
            replacement = "子どもたち"
            highlight_replacements.append((original, replacement, "表記を適切に修正"))
            corrections.append(f"- 3行目: ({original}) -> ({replacement}): 表記を適切に修正")
        
        if "増加期傾向" in corrected_text:
            original = "増加期傾向"
            replacement = "増加傾向"
            highlight_replacements.append((original, replacement, "不自然な表現の修正"))
            corrections.append(f"- 3行目: ({original}) -> ({replacement}): 不自然な表現の修正")
        
        if "思い悩むことでしょ" in corrected_text:
            original = "思い悩むことでしょ"
            replacement = "思い悩むことでしょう"
            highlight_replacements.append((original, replacement, "言葉を適切に修正"))
            corrections.append(f"- 11行目: ({original}) -> ({replacement}): 言葉を適切に修正")
        
        if "小学8年生" in corrected_text:
            original = "小学8年生"
            replacement = "中学2年生"
            highlight_replacements.append((original, replacement, "誤り修正（小学校は6年間）"))
            corrections.append(f"- 12行目: ({original}) -> ({replacement}): 誤り修正（小学校は6年間）")
            
        # 必ず検出できるように、テスト文章の内容に完全一致する修正を追加
        if "不登校のこどもたち" in corrected_text:
            original = "不登校のこどもたち"
            replacement = "不登校の子どもたち"
            highlight_replacements.append((original, replacement, "表記を適切に修正"))
            corrections.append(f"- 3行目: ({original}) -> ({replacement}): 表記を適切に修正")
            
        if "法則によると" in corrected_text:
            original = "法則によると"
            replacement = "定義によると"
            highlight_replacements.append((original, replacement, "適切な表現に修正"))
            corrections.append(f"- 5行目: ({original}) -> ({replacement}): 適切な表現に修正")
            
        if "経済敵な理由" in corrected_text:
            original = "経済敵な理由"
            replacement = "経済的な理由"
            highlight_replacements.append((original, replacement, "誤字修正"))
            corrections.append(f"- 5行目: ({original}) -> ({replacement}): 誤字修正")
            
        if "強質に入れなかったり" in corrected_text:
            original = "強質に入れなかったり"
            replacement = "教室に入れなかったり"
            highlight_replacements.append((original, replacement, "誤字修正"))
            corrections.append(f"- 9行目: ({original}) -> ({replacement}): 誤字修正")

        # 修正箇所に直接ハイライトを追加
        highlighted_text = corrected_text
        for original, replacement, reason in highlight_replacements:
            # 校正前のテキストをハイライト化
            # HTMLタグをそのままの文字列として表示するために、ハイライト処理でもエスケープする
            highlight_html = (
                f'<span class="correction-span">'
                f'<span class="correction-text">{original}</span>'
                f'<div class="correction-tooltip">'
                f'<span class="original-text">{html.escape(original)}</span><br>'
                f'<span class="corrected-text">{html.escape(replacement)}</span><br>'
                f'<span class="reason-text">{reason}</span><br>'
                f'<button class="apply-correction">修正する</button>'
                f'</div>'
                f'</span>'
            )
            # 元のテキストをハイライト付きのHTMLに置換
            highlighted_text = highlighted_text.replace(original, highlight_html)
            # 実際の修正を適用 (ハイライト処理のために元のテキストをそのまま残す)
            corrected_text = corrected_text.replace(original, replacement)
        
        # 修正箇所のフォーマット
        corrections_text = self.format_corrections(corrections)
        
        end_time = time.time()
        completion_time = end_time - start_time
        
        # 入出力トークン数とコスト計算
        input_tokens = self.count_tokens(text)
        output_tokens = self.count_tokens(highlighted_text + corrections_text)
        total_cost = self.calculate_cost(input_tokens, output_tokens)
        
        cost_info = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_cost": total_cost
        }
        
        return highlighted_text, corrections_text, completion_time, cost_info 