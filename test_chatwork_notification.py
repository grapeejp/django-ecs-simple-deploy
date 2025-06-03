#!/usr/bin/env python3
"""
チャットワーク通知機能のテストスクリプト
"""

import os
import sys
import django
from datetime import datetime

# Djangoの設定をロード
sys.path.append('app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# チャットワーク通知サービスをインポート
from proofreading_ai.services.notification_service import ChatworkNotificationService

def test_chatwork_connection():
    """
    チャットワーク接続テスト
    """
    print("🧪 チャットワーク通知機能テスト開始")
    print("=" * 50)
    
    # 環境変数の確認
    api_token = os.environ.get('CHATWORK_API_TOKEN')
    room_id = os.environ.get('CHATWORK_ROOM_ID')
    
    print(f"📋 設定確認:")
    print(f"   - API Token: {'設定済み' if api_token else '未設定'}")
    print(f"   - Room ID: {'設定済み' if room_id else '未設定'}")
    
    if not api_token or not room_id:
        print("❌ チャットワーク設定が不完全です")
        print("\n💡 設定方法:")
        print("   export CHATWORK_API_TOKEN='your-token-here'")
        print("   export CHATWORK_ROOM_ID='your-room-id-here'")
        return False
    
    # サービスのインスタンス作成
    chatwork_service = ChatworkNotificationService()
    
    print(f"\n📡 接続テスト実行中...")
    
    # 接続テストの実行
    try:
        success = chatwork_service.test_connection()
        if success:
            print("✅ チャットワーク通知機能が正常に動作しています")
            return True
        else:
            print("❌ チャットワーク通知機能でエラーが発生しました")
            return False
    except Exception as e:
        print(f"❌ テスト実行エラー: {str(e)}")
        return False

def test_error_notification():
    """
    エラー通知のテスト
    """
    print("\n🚨 エラー通知テスト")
    print("-" * 30)
    
    chatwork_service = ChatworkNotificationService()
    
    if not chatwork_service.is_configured():
        print("❌ チャットワーク設定が不完全のため、テストをスキップします")
        return False
    
    # テスト用のエラー通知
    try:
        context = {
            "function_name": "test_error_notification",
            "error_type": "TestError",
            "test_mode": True,
            "timestamp": datetime.now().isoformat()
        }
        
        success = chatwork_service.send_error_notification(
            "TEST_ERROR",
            "これはテスト用のエラー通知です。実際のエラーではありません。",
            context
        )
        
        if success:
            print("✅ エラー通知テスト成功")
            return True
        else:
            print("❌ エラー通知テスト失敗")
            return False
            
    except Exception as e:
        print(f"❌ エラー通知テストでエラー: {str(e)}")
        return False

def test_warning_notification():
    """
    警告通知のテスト
    """
    print("\n⚠️ 警告通知テスト")
    print("-" * 30)
    
    chatwork_service = ChatworkNotificationService()
    
    if not chatwork_service.is_configured():
        print("❌ チャットワーク設定が不完全のため、テストをスキップします")
        return False
    
    try:
        context = {
            "test_mode": True,
            "timestamp": datetime.now().isoformat()
        }
        
        success = chatwork_service.send_warning_notification(
            "これはテスト用の警告通知です。実際の警告ではありません。",
            context
        )
        
        if success:
            print("✅ 警告通知テスト成功")
            return True
        else:
            print("❌ 警告通知テスト失敗")
            return False
            
    except Exception as e:
        print(f"❌ 警告通知テストでエラー: {str(e)}")
        return False

def main():
    """
    メイン関数
    """
    print("🔧 チャットワーク通知機能 統合テスト")
    print(f"⏰ 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("接続テスト", test_chatwork_connection),
        ("エラー通知テスト", test_error_notification),
        ("警告通知テスト", test_warning_notification),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}で予期しないエラー: {str(e)}")
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 総合結果: {passed}/{total} テスト成功")
    
    if passed == total:
        print("🎉 すべてのテストが成功しました！")
        print("✅ チャットワーク通知機能は正常に動作しています。")
    else:
        print("⚠️ 一部のテストが失敗しました。")
        print("💡 設定やネットワーク接続を確認してください。")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 