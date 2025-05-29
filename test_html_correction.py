#!/usr/bin/env python3
"""
HTMLタグ内誤字検出機能のテストスクリプト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from proofreading_ai.utils import protect_html_tags_advanced, restore_html_tags_advanced

def test_html_correction():
    """HTMLタグ内の誤字検出をテスト"""
    
    # テストケース1: class="comment" の誤字
    test_html = '<dv class="comment">２０２４年、増加期傾向にある</dv>'
    
    print("🧪 HTMLタグ内誤字検出テスト")
    print(f"📝 元テキスト: {test_html}")
    
    # HTMLタグ保護（改良版）
    protected_text, placeholders, html_tag_info = protect_html_tags_advanced(test_html)
    
    print(f"🛡️ 保護後テキスト: {protected_text}")
    print(f"📋 プレースホルダー: {placeholders}")
    print(f"🏷️ HTMLタグ情報: {html_tag_info}")
    
    # 模擬修正（本来はAIが行う）
    mock_corrections = [
        {
            'original': 'dv',
            'corrected': 'div',
            'reason': 'HTMLタグ名の誤字修正',
            'category': 'typo'
        },
        {
            'original': 'comment',
            'corrected': 'content',  
            'reason': 'クラス名の誤字修正',
            'category': 'typo'
        },
        {
            'original': '増加期傾向',
            'corrected': '増加傾向',
            'reason': '不要な「期」を削除',
            'category': 'typo'
        }
    ]
    
    print(f"🔧 模擬修正: {mock_corrections}")
    
    # HTMLタグ復元（修正適用）
    corrected_text = restore_html_tags_advanced(protected_text, placeholders, html_tag_info, mock_corrections)
    
    print(f"✅ 修正後テキスト: {corrected_text}")
    
    # 期待される結果
    expected = '<div class="content">２０２４年、増加傾向にある</div>'
    print(f"🎯 期待結果: {expected}")
    
    # 結果の検証
    if corrected_text == expected:
        print("✅ テスト成功！HTMLタグ内の誤字も正しく修正されました")
    else:
        print("❌ テスト失敗！期待した結果と異なります")
        print(f"差異: 実際={corrected_text}, 期待={expected}")

if __name__ == "__main__":
    test_html_correction() 