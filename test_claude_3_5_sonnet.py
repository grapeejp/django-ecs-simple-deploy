#!/usr/bin/env python3
"""
Claude 3.5 Sonnet 校正機能テストスクリプト
修正されたBedrockClientの動作確認
"""

import sys
import os
import json
import logging

# Djangoプロジェクトのパスを追加
sys.path.append('/Users/yanagimotoyasutoshi/Desktop/django-ecs-simple-deploy/app')

# Django設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from proofreading_ai.services.bedrock_client import BedrockClient

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_claude_3_5_sonnet():
    """Claude 3.5 Sonnetの校正機能をテスト"""
    
    print("🚀 Claude 3.5 Sonnet 校正機能テスト開始")
    print("=" * 60)
    
    try:
        # BedrockClientの初期化
        print("🔧 BedrockClient初期化中...")
        client = BedrockClient()
        print(f"✅ 使用モデル: {client.model_id}")
        print(f"📊 プロファイル: {client.profile_info['name']}")
        
        # テスト用テキスト（HTMLタグ含む）
        test_text = """
        <h1>テスト文章</h1>
        <p>これは校正のテストです。いくつかの間違いが含まれています。</p>
        <ul>
            <li>誤字脱字のテスト: こんにちわ（正しくは「こんにちは」）</li>
            <li>表記ゆれのテスト: サーバー/サーバ</li>
            <li>言い回しのテスト: とても良いです（より自然な表現に）</li>
        </ul>
        <p>この文章を校正して、より読みやすくしてください。</p>
        """
        
        print("\n📝 テスト用テキスト:")
        print(test_text)
        
        # 校正実行
        print("\n🎯 校正処理開始...")
        
        corrected_text, tool_uses, usage, model, completion_time, cost_info = client.proofread_text(
            text=test_text,
            replacement_dict={},
            temperature=0.1,
            top_p=0.7
        )
        
        print("✅ 校正処理完了!")
        print(f"⏱️ 処理時間: {completion_time:.2f}秒")
        print(f"💰 コスト: {cost_info.get('total_cost', 0):.2f}円")
        print(f"🤖 使用モデル: {model}")
        
        print("\n📄 校正結果:")
        print("-" * 40)
        print(corrected_text)
        print("-" * 40)
        
        print(f"\n📊 詳細情報:")
        print(f"   - 入力トークン: {cost_info.get('input_tokens', 0)}")
        print(f"   - 出力トークン: {cost_info.get('output_tokens', 0)}")
        print(f"   - プロファイルタイプ: {cost_info.get('profile_type', '不明')}")
        
        # 結果をファイルに保存
        result_data = {
            "test_text": test_text,
            "corrected_text": corrected_text,
            "model": model,
            "completion_time": completion_time,
            "cost_info": cost_info,
            "usage": usage
        }
        
        with open("claude_3_5_sonnet_test_result.json", "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)
        
        print("\n💾 テスト結果をclaude_3_5_sonnet_test_result.jsonに保存しました")
        
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {str(e)}")
        import traceback
        print(f"📋 スタックトレース:\n{traceback.format_exc()}")
        return False

def test_html_protection():
    """HTMLタグ保護機能のテスト"""
    
    print("\n🛡️ HTMLタグ保護機能テスト")
    print("-" * 30)
    
    try:
        from proofreading_ai.utils import protect_html_tags, restore_html_tags
        
        test_html = '<h1>タイトル</h1><p>本文です。<strong>強調</strong>テキスト。</p>'
        
        print(f"元のHTML: {test_html}")
        
        # HTMLタグを保護
        protected_text, placeholders = protect_html_tags(test_html)
        print(f"保護後: {protected_text}")
        print(f"プレースホルダー: {placeholders}")
        
        # HTMLタグを復元
        restored_text = restore_html_tags(protected_text, placeholders)
        print(f"復元後: {restored_text}")
        
        # 元のテキストと復元後が一致するかチェック
        if test_html == restored_text:
            print("✅ HTMLタグ保護・復元: 成功")
            return True
        else:
            print("❌ HTMLタグ保護・復元: 失敗")
            return False
            
    except Exception as e:
        print(f"❌ HTMLタグ保護テストエラー: {str(e)}")
        return False

def main():
    """メイン実行関数"""
    
    print("🧪 Claude 3.5 Sonnet 校正AIテストスイート")
    print("=" * 60)
    
    # テスト実行
    tests = [
        ("HTMLタグ保護機能", test_html_protection),
        ("Claude 3.5 Sonnet校正機能", test_claude_3_5_sonnet)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}テスト実行中...")
        result = test_func()
        results.append((test_name, result))
        
        if result:
            print(f"✅ {test_name}: 成功")
        else:
            print(f"❌ {test_name}: 失敗")
    
    # 最終結果
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 総合結果: {success_count}/{total_count} テスト成功")
    
    if success_count == total_count:
        print("🎉 すべてのテストが成功しました！")
        print("🚀 校正AIアプリは正常に動作します")
    else:
        print("⚠️ 一部のテストが失敗しました")
        print("🔧 問題を確認して修正してください")

if __name__ == "__main__":
    main() 