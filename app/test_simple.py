#!/usr/bin/env python
"""
シンプルテスト: HTMLタグ誤字修正のみ
"""
import os
import sys
import django

# Django設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from proofreading_ai.services.bedrock_client import BedrockClient

def test_simple():
    print("🧪 シンプルテスト: HTMLタグ誤字修正のみ")
    print("=" * 40)
    
    client = BedrockClient()
    
    # シンプルテスト: HTMLタグ誤字のみ
    test_text = '<dv>こんにちは</dv>'
    print(f"入力: {test_text}")
    
    try:
        result = client.proofread_text(test_text)
        print("=" * 20)
        print("校正結果:")
        print(result[0])
        print("")
        
        # 結果確認
        if '<div>' in result[0]:
            print("✅ 成功: HTMLタグ誤字修正が動作！")
        else:
            print("❌ 失敗: HTMLタグ誤字修正が動作していません")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    test_simple() 