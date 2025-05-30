#!/usr/bin/env python3
import os
import sys
import django
import json
import time

# Django設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, 'app')
django.setup()

from proofreading_ai.services.bedrock_client import BedrockClient
from proofreading_ai.utils import protect_html_tags_advanced, restore_html_tags_advanced

def test_div_correction():
    """div系HTMLタグの修正をテスト"""
    
    print("🔧 DIV系HTMLタグ修正機能テスト開始")
    
    # テストケース
    test_cases = [
        {
            "name": "dvタグ修正テスト",
            "input": '<dv class="comment">２０２４年、増加期傾向にある</dv>',
            "expected_div_fix": "dv → div"
        },
        {
            "name": "divタグ属性誤字テスト", 
            "input": '<div clss="commnet">テストです</div>',
            "expected_attr_fix": "clss → class, commnet → comment"
        },
        {
            "name": "複数タグテスト",
            "input": '<dv><sepn clss="test">文章</sepn></dv>',
            "expected_fixes": "dv → div, sepn → span, clss → class"
        }
    ]
    
    client = BedrockClient()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"📝 入力: {test_case['input']}")
        
        # HTMLタグ保護処理をテスト
        protected_text, placeholders, html_tag_info = protect_html_tags_advanced(test_case['input'])
        print(f"🛡️ 保護後テキスト: {protected_text}")
        print(f"📋 プレースホルダー: {json.dumps(placeholders, ensure_ascii=False, indent=2)}")
        print(f"🏷️ HTMLタグ情報: {json.dumps(html_tag_info, ensure_ascii=False, indent=2)}")
        
        print(f"\n📤 Claude 4への送信テキスト:\n   {protected_text}")
        
        try:
            start_time = time.time()
            
            # 校正実行
            result, corrections, time_taken, cost_info = client.proofread_text(test_case['input'])
            
            print(f"\n✅ 校正結果: {result}")
            print(f"📝 修正箇所:")
            for correction in corrections:
                print(f"  - {correction.get('category', 'general')} | {correction.get('original', '')} -> {correction.get('corrected', '')}: {correction.get('reason', '')}")
            
            print(f"⏱️ 処理時間: {time_taken:.1f}秒")
            print(f"💰 コスト: {cost_info.get('total_cost', 0):.2f}円")
            print(f"🤖 使用モデル: {cost_info.get('model_id', 'unknown')}")
            
            # 期待される修正があるかチェック
            original_words = [c.get('original', '') for c in corrections]
            if 'dv' in test_case['input'] and 'dv' not in original_words:
                print("⚠️ 警告: 'dv' → 'div' の修正が見つかりません")
            if 'clss' in test_case['input'] and 'clss' not in original_words:
                print("⚠️ 警告: 'clss' → 'class' の修正が見つかりません")
                
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            import traceback
            print(f"📋 スタックトレース:\n{traceback.format_exc()}")
        
        print("-" * 80)

if __name__ == "__main__":
    test_div_correction() 