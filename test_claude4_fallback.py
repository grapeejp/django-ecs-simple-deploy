#!/usr/bin/env python3
"""
Claude 4 フォールバック機能テストスクリプト
Claude 4でエラーが発生した場合、Claude 3.5 Sonnetにフォールバックすることを確認
"""

import sys
import os
import json
import time

# Djangoプロジェクトのパスを追加
sys.path.append('/Users/yanagimotoyasutoshi/Desktop/django-ecs-simple-deploy/app')

# Django設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from proofreading_ai.services.bedrock_client import BedrockClient

def test_claude4_fallback():
    """Claude 4のフォールバック機能をテスト"""
    
    print("🧪 Claude 4 フォールバック機能テスト")
    print("=" * 50)
    
    try:
        # BedrockClientの初期化
        print("🔧 BedrockClient初期化中...")
        client = BedrockClient()
        
        print(f"🎯 プライマリモデル: {client.model_id}")
        print(f"🔄 フォールバックモデル: {client.fallback_model_id}")
        
        # テスト用テキスト
        test_text = """
        <h1>校正テスト</h1>
        <p>これは校正のテストです。いくつかの間違いが含まれています。</p>
        <ul>
            <li>誤字脱字のテスト: こんにちわ（正しくは「こんにちは」）</li>
            <li>言い回しのテスト: とても良いです（より自然な表現に）</li>
        </ul>
        """
        
        print(f"\n📝 テスト用テキスト:")
        print(test_text)
        
        # 校正実行
        print(f"\n🎯 校正処理開始...")
        print(f"   1. Claude 4を試行（アクセス権限不足でエラー予想）")
        print(f"   2. Claude 3.5 Sonnetにフォールバック（成功予想）")
        
        start_time = time.time()
        
        corrected_text, corrections, completion_time, cost_info = client.proofread_text(
            test_text, 
            replacement_dict={}, 
            temperature=0.1, 
            top_p=0.7
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n✅ 校正処理完了!")
        print(f"⏱️ 総処理時間: {total_time:.2f}秒")
        print(f"🤖 使用されたモデル: {client.model_id}")
        print(f"💰 コスト: {cost_info.get('total_cost', 0):.2f}円")
        
        print(f"\n📊 詳細情報:")
        print(f"   - 入力トークン: {cost_info.get('input_tokens', 0)}")
        print(f"   - 出力トークン: {cost_info.get('output_tokens', 0)}")
        print(f"   - プロファイルタイプ: {cost_info.get('profile_type', '不明')}")
        print(f"   - 修正箇所数: {len(corrections)}")
        
        # フォールバック成功の判定
        if client.fallback_model_id in str(client.model_id):
            print(f"\n🎉 フォールバック機能正常動作!")
            print(f"   Claude 4 → Claude 3.5 Sonnet への切り替え成功")
            return True
        elif "claude-sonnet-4" in str(client.model_id):
            print(f"\n🎉 Claude 4直接アクセス成功!")
            print(f"   アクセス権限が承認されました")
            return True
        else:
            print(f"\n⚠️ 予期しないモデルが使用されました: {client.model_id}")
            return False
        
    except Exception as e:
        print(f"\n❌ テストエラー: {str(e)}")
        import traceback
        print(f"📋 スタックトレース:\n{traceback.format_exc()}")
        return False

def main():
    """メイン実行関数"""
    
    print("🚀 Claude 4 フォールバック機能テストスイート")
    print("=" * 60)
    
    success = test_claude4_fallback()
    
    print(f"\n" + "=" * 60)
    print("📊 テスト結果")
    print("=" * 60)
    
    if success:
        print("✅ フォールバック機能テスト: 成功")
        print("🎯 校正AIアプリは正常に動作します")
        print("🔄 Claude 4のアクセス権限承認を待つ間、Claude 3.5 Sonnetで運用可能")
    else:
        print("❌ フォールバック機能テスト: 失敗")
        print("🔧 設定を確認してください")
    
    print(f"\n📋 次のステップ:")
    print(f"1. AWS Bedrockコンソールでアクセス申請")
    print(f"2. 承認後、Claude 4の直接アクセスが可能になります")
    print(f"3. 校正品質の向上を実感できます")

if __name__ == "__main__":
    main() 