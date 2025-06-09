#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
校正AIエラー通知機能テストスクリプト

1. 校正API呼び出しでエラーを発生させる
2. Chatwork通知が自動送信されることを確認
3. 日本時間表示とエラー詳細情報が含まれることを確認
"""

import os
import sys
import json
import requests
import traceback
from datetime import datetime, timezone, timedelta

# Djangoアプリケーションの設定
sys.path.append('app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

# 日本時間を取得する関数
def get_japan_time():
    """日本時間（JST +9時間）を取得"""
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst)

def test_proofread_api_error():
    """校正APIでエラーを発生させるテスト"""
    print("🧪 校正API エラー通知テスト開始")
    print(f"📅 テスト実行時刻: {get_japan_time().strftime('%Y年%m月%d日 %H時%M分')}")
    
    # Docker環境の校正APIエンドポイント
    url = "http://localhost:8000/proofreading_ai/proofread/"
    
    # 不正なリクエストデータ（意図的にエラーを発生させる）
    test_cases = [
        {
            "name": "JSONパースエラーテスト",
            "data": "invalid json data",  # 不正なJSON
            "content_type": "application/json"
        },
        {
            "name": "空のテキストエラーテスト", 
            "data": json.dumps({"text": "", "temperature": 0.1, "top_p": 0.7}),
            "content_type": "application/json"
        },
        {
            "name": "異常な温度パラメータエラーテスト",
            "data": json.dumps({"text": "テストテキスト", "temperature": "invalid", "top_p": 0.7}),
            "content_type": "application/json"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎯 テストケース {i}: {test_case['name']}")
        
        try:
            response = requests.post(
                url,
                data=test_case["data"],
                headers={"Content-Type": test_case["content_type"]},
                timeout=30
            )
            
            print(f"📊 HTTPステータス: {response.status_code}")
            
            try:
                result = response.json()
                print(f"📝 レスポンス: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if not result.get("success", True):
                    print(f"✅ 期待通りエラーが発生: {result.get('error', '不明なエラー')}")
                    print("📤 Chatwork通知が送信されているはずです")
                else:
                    print(f"⚠️ 予期しない成功レスポンス")
                    
            except json.JSONDecodeError:
                print(f"❌ JSONレスポンス解析失敗")
                print(f"📝 生レスポンス: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ リクエストエラー: {str(e)}")
            print("📤 アプリケーションレベルでChatwork通知が送信されているはずです")
            
        except Exception as e:
            print(f"❌ テスト実行エラー: {str(e)}")
            print(f"📋 エラー詳細:\n{traceback.format_exc()}")

def test_bedrock_connection_error():
    """BedrockClient接続エラーテスト"""
    print("\n🧪 BedrockClient エラー通知テスト開始")
    
    try:
        from proofreading_ai.services.bedrock_client import BedrockClient
        
        # 一時的にAWS環境変数を削除してエラーを発生させる
        original_region = os.environ.get("AWS_REGION")
        os.environ.pop("AWS_REGION", None)
        
        print("🔧 AWS_REGION環境変数を一時削除")
        
        # BedrockClientの初期化（エラーが発生するはず）
        try:
            client = BedrockClient()
            print("⚠️ 予期しない成功: BedrockClient初期化が成功しました")
        except Exception as e:
            print(f"✅ 期待通りエラーが発生: {str(e)}")
            print("📤 Chatwork通知が送信されているはずです")
        
        # 環境変数を復元
        if original_region:
            os.environ["AWS_REGION"] = original_region
            print(f"🔄 AWS_REGION環境変数を復元: {original_region}")
            
    except ImportError as e:
        print(f"❌ BedrockClientインポートエラー: {str(e)}")
    except Exception as e:
        print(f"❌ テスト実行エラー: {str(e)}")
        print(f"📋 エラー詳細:\n{traceback.format_exc()}")

def main():
    """メインテスト実行"""
    print("🚀 校正AI エラー通知機能 総合テスト開始")
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
    test_proofread_api_error()
    test_bedrock_connection_error()
    
    print("\n🏁 テスト完了")
    print("📱 Chatworkルームを確認して、エラー通知が送信されているか確認してください")
    print(f"🕐 テスト終了時刻: {get_japan_time().strftime('%Y年%m月%d日 %H時%M分')}")

if __name__ == "__main__":
    main() 