#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
校正AIエラー通知機能 直接テストスクリプト

1. Django内部から直接エラーを発生させる
2. Chatwork通知が自動送信されることを確認
3. エラー詳細情報が含まれることを確認
"""

import os
import sys
import json
import traceback
from datetime import datetime, timezone, timedelta

# Djangoアプリケーションの設定
sys.path.append('app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from proofreading_ai.services.notification_service import ChatworkNotificationService

def get_japan_time():
    """日本時間（JST +9時間）を取得"""
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst)

def test_chatwork_error_notification():
    """Chatworkエラー通知直接テスト"""
    print("🧪 Chatworkエラー通知 直接テスト開始")
    print(f"📅 テスト実行時刻: {get_japan_time().strftime('%Y年%m月%d日 %H時%M分')}")
    
    try:
        # ChatworkNotificationServiceインスタンス作成
        chatwork_service = ChatworkNotificationService()
        
        # 設定確認
        if not chatwork_service.is_configured():
            print("❌ Chatwork設定が不完全です")
            return False
        
        print("✅ Chatwork設定確認完了")
        
        # テスト用エラー情報
        error_context = {
            'function': 'test_error_direct.py',
            'error_type': 'TestException',
            'test_mode': True,
            'timestamp': get_japan_time().isoformat(),
            'client_ip': '127.0.0.1',
            'user_agent': 'ErrorNotificationTest/1.0',
            'text_length': 25,
            'temperature': 0.1,
            'top_p': 0.7,
            'stack_trace': 'Test stack trace for error notification'
        }
        
        # エラー通知送信テスト
        print("📤 エラー通知送信テスト実行中...")
        
        result = chatwork_service.send_error_notification(
            error_type="PROOFREAD_TEST_ERROR",
            error_message="校正AIエラー通知機能のテストです。この通知は自動生成されました。",
            context=error_context
        )
        
        if result:
            print("✅ エラー通知送信成功")
        else:
            print("❌ エラー通知送信失敗")
            
        return result
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {str(e)}")
        print(f"📋 エラー詳細:\n{traceback.format_exc()}")
        return False

def test_mock_proofread_error():
    """模擬校正エラーテスト"""
    print("\n🧪 模擬校正エラーテスト開始")
    
    try:
        # Django viewsからのインポート
        from django.http import HttpRequest
        from proofreading_ai.views import proofread
        import json
        
        # 模擬リクエスト作成（不正なJSON）
        request = HttpRequest()
        request.method = 'POST'
        request.META['CONTENT_TYPE'] = 'application/json'
        request.META['HTTP_USER_AGENT'] = 'ErrorNotificationTest/1.0'
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        # 不正なJSONボディを設定
        request._body = '{"text": "テスト", "temperature": "invalid_value"}'.encode('utf-8')
        
        print("📝 不正なリクエストデータで校正API呼び出し")
        
        # 校正関数呼び出し（エラーが発生するはず）
        response = proofread(request)
        
        print(f"📊 レスポンス: {response.content.decode('utf-8')}")
        
        # レスポンス解析
        response_data = json.loads(response.content.decode('utf-8'))
        
        if not response_data.get('success', True):
            print("✅ 期待通りエラーが発生しました")
            print(f"🚨 エラー内容: {response_data.get('error', '不明')}")
            print("📤 Chatwork通知が送信されているはずです")
            return True
        else:
            print("⚠️ 予期しない成功レスポンス")
            return False
            
    except Exception as e:
        print(f"❌ 模擬テストエラー: {str(e)}")
        print(f"📋 エラー詳細:\n{traceback.format_exc()}")
        return False

def main():
    """メインテスト実行"""
    print("🚀 校正AI エラー通知機能 直接テスト開始")
    print("="*60)
    
    # 環境変数確認
    api_token = os.environ.get("CHATWORK_API_TOKEN")
    room_id = os.environ.get("CHATWORK_ROOM_ID")
    
    if not api_token or not room_id:
        print("❌ Chatwork環境変数が設定されていません")
        print(f"API Token: {'設定済み' if api_token else '未設定'}")
        print(f"Room ID: {'設定済み' if room_id else '未設定'}")
        return
    
    print(f"✅ Chatwork設定確認完了")
    print(f"   - API Token: {api_token[:10]}...")
    print(f"   - Room ID: {room_id}")
    
    # テスト実行
    test1_result = test_chatwork_error_notification()
    test2_result = test_mock_proofread_error()
    
    print("\n🏁 テスト完了")
    print(f"📊 結果サマリー:")
    print(f"   - 直接エラー通知テスト: {'✅ 成功' if test1_result else '❌ 失敗'}")
    print(f"   - 模擬校正エラーテスト: {'✅ 成功' if test2_result else '❌ 失敗'}")
    print("📱 Chatworkルームを確認して、エラー通知が送信されているか確認してください")
    print(f"🕐 テスト終了時刻: {get_japan_time().strftime('%Y年%m月%d日 %H時%M分')}")

if __name__ == "__main__":
    main() 