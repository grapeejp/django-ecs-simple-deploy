#!/usr/bin/env python3
"""
Claude Sonnet 4 アクセス権限申請スクリプト
AWS Bedrockコンソールでの手動申請をサポートするためのガイド
"""

import boto3
import json
import os
import sys
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_claude4_access():
    """Claude 4のアクセス状況を確認"""
    
    print("🔍 Claude Sonnet 4 アクセス状況確認")
    print("=" * 50)
    
    try:
        # Bedrockクライアント作成
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-northeast-1')
        
        # Claude 4のモデルID
        claude4_model_id = "anthropic.claude-sonnet-4-20250514-v1:0"
        
        # テスト用ペイロード
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 10,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "Hello"}]
                }
            ]
        }
        
        # アクセステスト
        print(f"🎯 テスト対象: {claude4_model_id}")
        
        response = bedrock_runtime.invoke_model(
            modelId=claude4_model_id,
            body=json.dumps(payload)
        )
        
        print("✅ Claude Sonnet 4: アクセス可能!")
        return True
        
    except Exception as e:
        if 'AccessDenied' in str(e):
            print("❌ Claude Sonnet 4: アクセス権限不足")
            print(f"   エラー: {str(e)}")
            return False
        else:
            print(f"❌ 予期しないエラー: {str(e)}")
            return False

def generate_access_request_info():
    """アクセス申請に必要な情報を生成"""
    
    print("\n📋 Claude Sonnet 4 アクセス申請情報")
    print("=" * 50)
    
    # AWS アカウント情報取得
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        account_id = identity.get('Account')
        user_arn = identity.get('Arn')
        
        print(f"🆔 AWSアカウントID: {account_id}")
        print(f"👤 ユーザーARN: {user_arn}")
        
    except Exception as e:
        print(f"❌ AWS情報取得エラー: {str(e)}")
        account_id = "不明"
        user_arn = "不明"
    
    # 申請情報
    request_info = {
        "model_id": "anthropic.claude-sonnet-4-20250514-v1:0",
        "model_name": "Claude Sonnet 4",
        "region": "ap-northeast-1",
        "account_id": account_id,
        "user_arn": user_arn,
        "use_case": "Japanese text proofreading application for business documents",
        "business_justification": "Need Claude 4's advanced reasoning capabilities for high-quality Japanese text corrections",
        "expected_usage": "校正AI専用アプリケーション - 月間1000リクエスト程度",
        "application_type": "Production business application"
    }
    
    print(f"\n📄 申請用情報:")
    print(json.dumps(request_info, indent=2, ensure_ascii=False))
    
    # ファイルに保存
    with open("claude4_access_request.json", "w", encoding="utf-8") as f:
        json.dump(request_info, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 申請情報をclaude4_access_request.jsonに保存しました")
    
    return request_info

def print_manual_steps():
    """手動申請の手順を表示"""
    
    print("\n🛠️ Claude Sonnet 4 アクセス申請手順")
    print("=" * 50)
    
    steps = [
        "1. AWS Bedrockコンソールにアクセス",
        "   https://ap-northeast-1.console.aws.amazon.com/bedrock/",
        "",
        "2. 左メニューから「Model access」を選択",
        "",
        "3. 「Request model access」ボタンをクリック",
        "",
        "4. Claude Sonnet 4を検索・選択",
        "   - Model ID: anthropic.claude-sonnet-4-20250514-v1:0",
        "   - Model Name: Claude Sonnet 4",
        "",
        "5. Use caseを記入:",
        "   「Japanese text proofreading application for business documents.",
        "    Need Claude 4's advanced reasoning capabilities for high-quality corrections.」",
        "",
        "6. 申請を送信",
        "",
        "7. 承認を待つ（通常1-3営業日）",
        "",
        "8. 承認後、アプリケーションで使用可能"
    ]
    
    for step in steps:
        print(step)

def check_alternative_regions():
    """他のリージョンでのClaude 4利用可能性を確認"""
    
    print("\n🌏 他リージョンでのClaude 4確認")
    print("=" * 50)
    
    regions = [
        "us-east-1",      # バージニア北部
        "us-west-2",      # オレゴン
        "eu-west-1",      # アイルランド
        "ap-southeast-1", # シンガポール
        "ap-southeast-2"  # シドニー
    ]
    
    claude4_model_id = "anthropic.claude-sonnet-4-20250514-v1:0"
    
    for region in regions:
        try:
            bedrock = boto3.client('bedrock', region_name=region)
            models = bedrock.list_foundation_models()
            
            claude4_available = any(
                model['modelId'] == claude4_model_id 
                for model in models.get('modelSummaries', [])
            )
            
            if claude4_available:
                print(f"✅ {region}: Claude 4利用可能")
                
                # アクセステスト
                try:
                    bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
                    payload = {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": [{"type": "text", "text": "test"}]}]
                    }
                    
                    bedrock_runtime.invoke_model(
                        modelId=claude4_model_id,
                        body=json.dumps(payload)
                    )
                    print(f"   🎯 {region}: アクセス可能!")
                    
                except Exception as e:
                    if 'AccessDenied' in str(e):
                        print(f"   ❌ {region}: アクセス権限不足")
                    else:
                        print(f"   ⚠️ {region}: {str(e)}")
            else:
                print(f"❌ {region}: Claude 4利用不可")
                
        except Exception as e:
            print(f"❌ {region}: エラー - {str(e)}")

def main():
    """メイン実行関数"""
    
    print("🚀 Claude Sonnet 4 アクセス申請サポートツール")
    print("=" * 60)
    
    # 1. 現在のアクセス状況確認
    has_access = check_claude4_access()
    
    if has_access:
        print("\n🎉 Claude Sonnet 4は既に利用可能です！")
        print("🔧 アプリケーションの設定を確認してください")
        return
    
    # 2. 申請情報生成
    generate_access_request_info()
    
    # 3. 手動申請手順表示
    print_manual_steps()
    
    # 4. 他リージョン確認
    check_alternative_regions()
    
    print("\n" + "=" * 60)
    print("📞 サポート情報")
    print("=" * 60)
    print("- AWS Support: https://console.aws.amazon.com/support/")
    print("- Bedrock Documentation: https://docs.aws.amazon.com/bedrock/")
    print("- 申請状況確認: AWS Bedrockコンソール > Model access")
    
    print("\n🔄 申請完了後の確認方法:")
    print("python request_claude4_access.py")

if __name__ == "__main__":
    main() 