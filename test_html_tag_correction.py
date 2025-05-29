#!/usr/bin/env python3
"""
HTMLタグ内誤字検出機能のテストスクリプト
"""

import os
import sys
import django
from pathlib import Path

# Django設定
sys.path.append(str(Path(__file__).parent / 'app'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from proofreading_ai.utils import protect_html_tags_advanced, restore_html_tags_advanced

def test_html_tag_correction():
    """HTMLタグ内誤字の検出・修正をテスト"""
    print("🔧 HTMLタグ内誤字検出機能テスト開始")
    
    # テスト用入力（HTMLタグ内に誤字を含む）
    test_input = '<dv class="comment">２０２４年、増加期傾向にある</dv>'
    print(f"📝 入力: {test_input}")
    
    # ステップ1: HTMLタグを保護（advanced版）
    protected_text, placeholders, html_tag_info = protect_html_tags_advanced(test_input)
    print(f"🛡️ 保護後テキスト: {protected_text}")
    print(f"📋 プレースホルダー: {placeholders}")
    print(f"🏷️ HTMLタグ情報: {html_tag_info}")
    
    # Claude 4に送信されるテキストはこの状態
    print(f"\n📤 Claude 4への送信テキスト:")
    print(f"   {protected_text}")
    
    # 想定される修正結果をシミュレート
    simulated_corrections = [
        {'original': 'dv', 'corrected': 'div', 'reason': 'HTMLタグ名の誤字修正'},
        {'original': 'comment', 'corrected': 'content', 'reason': 'クラス名の修正提案'},
        {'original': '増加期傾向', 'corrected': '増加傾向', 'reason': '不要な文字の削除'}
    ]
    print(f"\n🔧 想定される修正結果:")
    for correction in simulated_corrections:
        print(f"   {correction['original']} → {correction['corrected']} ({correction['reason']})")
    
    # ステップ2: HTMLタグを復元（修正適用）
    restored_text = restore_html_tags_advanced(protected_text, placeholders, html_tag_info, simulated_corrections)
    print(f"\n✅ 復元後テキスト: {restored_text}")
    
    # 期待される結果
    expected_result = '<div class="content">２０２４年、増加傾向にある</div>'
    print(f"🎯 期待される結果: {expected_result}")
    
    # 結果の確認
    if restored_text == expected_result:
        print("🎉 テスト成功！HTMLタグ内の誤字が正しく修正されました")
    else:
        print("❌ テスト失敗。結果が期待と異なります")
        print(f"   実際: {restored_text}")
        print(f"   期待: {expected_result}")
    
    return restored_text == expected_result

if __name__ == "__main__":
    test_html_tag_correction() 