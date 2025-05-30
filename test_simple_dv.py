#!/usr/bin/env python3
import os
import sys
import django

# Django設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, 'app')
django.setup()

from proofreading_ai.services.bedrock_client import BedrockClient

def test_simple_dv():
    """シンプルなdvタグのテスト"""
    print("🔧 シンプルなdvタグテスト開始")
    
    # 最もシンプルなテストケース
    test_input = '<dv class="comment">２０２４年、増加期傾向にある</dv>'
    print(f"📝 入力: {test_input}")
    
    client = BedrockClient()
    
    try:
        result, corrections, time_taken, cost_info = client.proofread_text(test_input)
        print(f"\n✅ 校正結果: {result}")
        print(f"📝 修正箇所: {len(corrections)}件")
        for correction in corrections:
            print(f"  - {correction.get('category', 'general')} | {correction.get('original', '')} -> {correction.get('corrected', '')}")
            
    except Exception as e:
        print(f"❌ エラー: {str(e)}")

if __name__ == "__main__":
    test_simple_dv() 