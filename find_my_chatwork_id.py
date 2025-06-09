#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chatwork 自分のユーザーID調べるスクリプト

1. /me エンドポイントで自分の情報を取得
2. /contacts エンドポイントで連絡先一覧を取得
3. 個人宛メッセージ送信のテスト
"""

import os
import sys
import json
import requests
import traceback
from datetime import datetime, timezone, timedelta

def get_japan_time():
    """日本時間（JST +9時間）を取得"""
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst)

def get_my_chatwork_info():
    """自分のChatwork情報を取得"""
    print("🔍 Chatwork 自分の情報取得開始")
    print(f"📅 実行時刻: {get_japan_time().strftime('%Y年%m月%d日 %H時%M分')}")
    
    api_token = os.environ.get("CHATWORK_API_TOKEN")
    if not api_token:
        print("❌ CHATWORK_API_TOKEN環境変数が設定されていません")
        return None
    
    print(f"✅ APIトークン: {api_token[:10]}...")
    
    headers = {
        "X-ChatWorkToken": api_token,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        # 1. 自分の情報を取得
        print("\n📋 /me エンドポイントで自分の情報を取得中...")
        me_response = requests.get("https://api.chatwork.com/v2/me", headers=headers)
        
        if me_response.status_code == 200:
            me_info = me_response.json()
            print("✅ 自分の情報取得成功:")
            print(f"   - アカウントID: {me_info.get('account_id')}")
            print(f"   - ルームID: {me_info.get('room_id')}")
            print(f"   - 名前: {me_info.get('name')}")
            print(f"   - チャットワークID: {me_info.get('chatwork_id')}")
            print(f"   - 組織ID: {me_info.get('organization_id')}")
            print(f"   - 組織名: {me_info.get('organization_name')}")
            print(f"   - 部署: {me_info.get('department')}")
            print(f"   - タイトル: {me_info.get('title')}")
            print(f"   - URL: {me_info.get('url')}")
            print(f"   - 紹介: {me_info.get('introduction')}")
            print(f"   - メール: {me_info.get('mail')}")
            print(f"   - 電話番号: {me_info.get('tel_organization')}")
            print(f"   - 携帯電話: {me_info.get('tel_extension')}")
            print(f"   - Skype: {me_info.get('skype')}")
            print(f"   - Facebook: {me_info.get('facebook')}")
            print(f"   - Twitter: {me_info.get('twitter')}")
            print(f"   - アバターURL: {me_info.get('avatar_image_url')}")
            print(f"   - ログイン名: {me_info.get('login_mail')}")
            
            # JSON形式でも出力
            print(f"\n📄 完全なJSON情報:")
            print(json.dumps(me_info, ensure_ascii=False, indent=2))
            
            return me_info
        else:
            print(f"❌ 自分の情報取得エラー: {me_response.status_code}")
            print(f"📝 エラー内容: {me_response.text}")
            return None
            
    except Exception as e:
        print(f"❌ API呼び出しエラー: {str(e)}")
        print(f"📋 エラー詳細:\n{traceback.format_exc()}")
        return None

def get_my_contacts():
    """連絡先一覧を取得"""
    print("\n🔍 連絡先一覧取得開始")
    
    api_token = os.environ.get("CHATWORK_API_TOKEN")
    headers = {
        "X-ChatWorkToken": api_token,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        print("📋 /contacts エンドポイントで連絡先一覧を取得中...")
        contacts_response = requests.get("https://api.chatwork.com/v2/contacts", headers=headers)
        
        if contacts_response.status_code == 200:
            contacts = contacts_response.json()
            print(f"✅ 連絡先取得成功: {len(contacts)}件")
            
            # 最初の5件を表示
            for i, contact in enumerate(contacts[:5], 1):
                print(f"\n📱 連絡先 {i}:")
                print(f"   - アカウントID: {contact.get('account_id')}")
                print(f"   - ルームID: {contact.get('room_id')}")
                print(f"   - 名前: {contact.get('name')}")
                print(f"   - チャットワークID: {contact.get('chatwork_id')}")
                print(f"   - 組織ID: {contact.get('organization_id')}")
                print(f"   - 組織名: {contact.get('organization_name')}")
                print(f"   - 部署: {contact.get('department')}")
            
            if len(contacts) > 5:
                print(f"\n... 他 {len(contacts) - 5}件の連絡先があります")
            
            # JSON形式でも出力
            print(f"\n📄 連絡先完全リスト:")
            print(json.dumps(contacts, ensure_ascii=False, indent=2))
            
            return contacts
        else:
            print(f"❌ 連絡先取得エラー: {contacts_response.status_code}")
            print(f"📝 エラー内容: {contacts_response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 連絡先取得エラー: {str(e)}")
        print(f"📋 エラー詳細:\n{traceback.format_exc()}")
        return None

def test_direct_message(my_info):
    """自分宛にダイレクトメッセージを送信テスト"""
    if not my_info:
        print("❌ 自分の情報が取得できていないため、ダイレクトメッセージテストをスキップします")
        return False
    
    print("\n🧪 自分宛ダイレクトメッセージ送信テスト開始")
    
    api_token = os.environ.get("CHATWORK_API_TOKEN")
    headers = {
        "X-ChatWorkToken": api_token,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # room_idを使用（自分の個人ルーム）
    my_room_id = my_info.get('room_id')
    if not my_room_id:
        print("❌ 自分のroom_idが取得できませんでした")
        return False
    
    print(f"📤 自分のルームID {my_room_id} にメッセージ送信中...")
    
    test_message = f"""🤖 【テスト通知】個人宛メッセージ
⏰ 送信時刻: {get_japan_time().strftime('%Y年%m月%d日 %H時%M分')}
📝 内容: Chatwork個人宛通知機能のテストです
✅ 成功: 自分宛にメッセージを送信できました！"""
    
    try:
        response = requests.post(
            f"https://api.chatwork.com/v2/rooms/{my_room_id}/messages",
            headers=headers,
            data={"body": test_message}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 自分宛メッセージ送信成功!")
            print(f"📝 メッセージID: {result.get('message_id')}")
            print("📱 Chatworkアプリで確認してください")
            return True
        else:
            print(f"❌ メッセージ送信エラー: {response.status_code}")
            print(f"📝 エラー内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ダイレクトメッセージ送信エラー: {str(e)}")
        print(f"📋 エラー詳細:\n{traceback.format_exc()}")
        return False

def main():
    """メイン処理"""
    print("🚀 Chatwork 自分のID調査 & 個人宛通知テスト開始")
    print("="*60)
    
    # 環境変数確認
    api_token = os.environ.get("CHATWORK_API_TOKEN")
    if not api_token:
        print("❌ CHATWORK_API_TOKEN環境変数が設定されていません")
        print("設定方法: export CHATWORK_API_TOKEN='your-api-token-here'")
        return
    
    # 1. 自分の情報取得
    my_info = get_my_chatwork_info()
    
    # 2. 連絡先一覧取得
    contacts = get_my_contacts()
    
    # 3. 自分宛ダイレクトメッセージテスト
    test_direct_message(my_info)
    
    print("\n🏁 調査完了")
    print("\n💡 個人宛通知を設定する方法:")
    if my_info:
        room_id = my_info.get('room_id')
        if room_id:
            print(f"   - 自分のroom_id: {room_id}")
            print("   - NotificationServiceで CHATWORK_ROOM_ID をこの値に設定")
            print(f"   - export CHATWORK_ROOM_ID='{room_id}'")
        else:
            print("   - room_idが取得できませんでした")
    
    print(f"\n🕐 処理終了時刻: {get_japan_time().strftime('%Y年%m月%d日 %H時%M分')}")

if __name__ == "__main__":
    main() 