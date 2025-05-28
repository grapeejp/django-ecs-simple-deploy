#!/usr/bin/env python3
"""
Claude 4 推論プロファイルARN自動検出スクリプト
作成されたClaude 4のARNを見つけて、BedrockClientを自動更新
"""

import boto3
import json
import os
import sys
import logging
import re

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_claude4_inference_profiles():
    """Claude 4関連の推論プロファイルを検索"""
    
    print("🔍 Claude 4 推論プロファイル検索開始")
    print("=" * 50)
    
    claude4_profiles = []
    
    try:
        bedrock = boto3.client('bedrock', region_name='ap-northeast-1')
        
        # 推論プロファイル一覧取得
        response = bedrock.list_inference_profiles()
        profiles = response.get('inferenceProfileSummaries', [])
        
        print(f"📋 検出された推論プロファイル数: {len(profiles)}")
        
        for profile in profiles:
            profile_id = profile.get('inferenceProfileId', '')
            profile_name = profile.get('inferenceProfileName', '')
            profile_arn = profile.get('inferenceProfileArn', '')
            models = profile.get('models', [])
            
            print(f"\n📄 プロファイル: {profile_name}")
            print(f"   ID: {profile_id}")
            print(f"   ARN: {profile_arn}")
            print(f"   モデル数: {len(models)}")
            
            # Claude 4関連かチェック
            is_claude4 = False
            for model in models:
                model_id = model.get('modelId', '')
                print(f"   - モデル: {model_id}")
                
                if 'claude-sonnet-4' in model_id or 'claude-4' in model_id:
                    is_claude4 = True
            
            if is_claude4 or 'claude-4' in profile_name.lower() or 'claude4' in profile_name.lower():
                claude4_profiles.append({
                    'id': profile_id,
                    'name': profile_name,
                    'arn': profile_arn,
                    'models': models
                })
                print(f"   ✅ Claude 4関連プロファイル発見!")
        
        return claude4_profiles
        
    except Exception as e:
        print(f"❌ 推論プロファイル検索エラー: {str(e)}")
        return []

def find_application_inference_profiles():
    """アプリケーション推論プロファイルを検索"""
    
    print("\n🔍 アプリケーション推論プロファイル検索")
    print("=" * 50)
    
    try:
        bedrock = boto3.client('bedrock', region_name='ap-northeast-1')
        
        # アプリケーション推論プロファイル一覧取得
        response = bedrock.list_application_inference_profiles()
        profiles = response.get('inferenceProfileSummaries', [])
        
        print(f"📋 アプリケーション推論プロファイル数: {len(profiles)}")
        
        claude4_app_profiles = []
        
        for profile in profiles:
            profile_id = profile.get('inferenceProfileId', '')
            profile_name = profile.get('inferenceProfileName', '')
            profile_arn = profile.get('inferenceProfileArn', '')
            
            print(f"\n📄 アプリケーションプロファイル: {profile_name}")
            print(f"   ID: {profile_id}")
            print(f"   ARN: {profile_arn}")
            
            # Claude 4関連かチェック
            if ('claude-4' in profile_name.lower() or 
                'claude4' in profile_name.lower() or 
                'proofreading' in profile_name.lower()):
                
                claude4_app_profiles.append({
                    'id': profile_id,
                    'name': profile_name,
                    'arn': profile_arn
                })
                print(f"   ✅ Claude 4関連アプリケーションプロファイル発見!")
        
        return claude4_app_profiles
        
    except Exception as e:
        print(f"❌ アプリケーション推論プロファイル検索エラー: {str(e)}")
        return []

def test_claude4_arn(arn):
    """指定されたARNでClaude 4のアクセステスト"""
    
    print(f"\n🧪 Claude 4 ARNテスト: {arn}")
    print("-" * 50)
    
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-northeast-1')
        
        # テスト用ペイロード
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 50,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "こんにちは。簡単なテストです。「はい」と答えてください。"}]
                }
            ]
        }
        
        # モデル呼び出し
        response = bedrock_runtime.invoke_model(
            modelId=arn,
            body=json.dumps(payload)
        )
        
        # レスポンス解析
        response_body = json.loads(response.get("body").read())
        content = response_body.get("content", [])
        
        test_response = ""
        for c in content:
            if c.get("type") == "text":
                test_response += c.get("text", "")
        
        print(f"✅ テスト成功!")
        print(f"📝 応答: {test_response[:100]}...")
        print(f"📊 使用情報: {response_body.get('usage', {})}")
        
        return True, test_response
        
    except Exception as e:
        print(f"❌ テスト失敗: {str(e)}")
        return False, str(e)

def update_bedrock_client(working_arn):
    """BedrockClientを正しいARNで更新"""
    
    print(f"\n🔧 BedrockClient更新: {working_arn}")
    print("=" * 50)
    
    try:
        # BedrockClientファイルを読み込み
        client_file = "app/proofreading_ai/services/bedrock_client.py"
        
        with open(client_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # model_idの行を検索・更新
        pattern = r'self\.model_id = ["\'].*?["\']'
        replacement = f'self.model_id = "{working_arn}"'
        
        updated_content = re.sub(pattern, replacement, content)
        
        # ファイルに書き戻し
        with open(client_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ BedrockClient更新完了")
        print(f"📄 ファイル: {client_file}")
        print(f"🎯 新しいモデルID: {working_arn}")
        
        return True
        
    except Exception as e:
        print(f"❌ BedrockClient更新エラー: {str(e)}")
        return False

def main():
    """メイン実行関数"""
    
    print("🚀 Claude 4 ARN自動検出・設定ツール")
    print("=" * 60)
    
    # 1. 推論プロファイル検索
    inference_profiles = find_claude4_inference_profiles()
    
    # 2. アプリケーション推論プロファイル検索
    app_profiles = find_application_inference_profiles()
    
    # 3. 全候補をテスト
    all_candidates = []
    
    # 推論プロファイルのARNを追加
    for profile in inference_profiles:
        all_candidates.append({
            'type': 'inference_profile',
            'arn': profile['arn'],
            'name': profile['name']
        })
    
    # アプリケーション推論プロファイルのARNを追加
    for profile in app_profiles:
        all_candidates.append({
            'type': 'application_inference_profile',
            'arn': profile['arn'],
            'name': profile['name']
        })
    
    # 手動で作成された可能性のあるARNも追加
    manual_candidates = [
        f"arn:aws:bedrock:ap-northeast-1:026090540679:inference-profile/proofreading-ai-claude-4",
        f"arn:aws:bedrock:ap-northeast-1:026090540679:application-inference-profile/proofreading-ai-claude-4",
        f"arn:aws:bedrock:ap-northeast-1:026090540679:inference-profile/claude-4",
        f"arn:aws:bedrock:ap-northeast-1:026090540679:application-inference-profile/claude-4"
    ]
    
    for arn in manual_candidates:
        all_candidates.append({
            'type': 'manual_candidate',
            'arn': arn,
            'name': 'Manual candidate'
        })
    
    print(f"\n🎯 テスト候補数: {len(all_candidates)}")
    
    # 4. 各候補をテスト
    working_arn = None
    
    for i, candidate in enumerate(all_candidates, 1):
        print(f"\n--- テスト {i}/{len(all_candidates)} ---")
        print(f"タイプ: {candidate['type']}")
        print(f"名前: {candidate['name']}")
        
        success, response = test_claude4_arn(candidate['arn'])
        
        if success:
            working_arn = candidate['arn']
            print(f"🎉 動作するARNを発見: {working_arn}")
            break
    
    # 5. BedrockClient更新
    if working_arn:
        print(f"\n🔧 BedrockClient自動更新")
        update_success = update_bedrock_client(working_arn)
        
        if update_success:
            print(f"\n✅ Claude 4設定完了!")
            print(f"🎯 使用ARN: {working_arn}")
            print(f"🚀 校正AIアプリでClaude 4が使用可能になりました")
            
            # 結果をファイルに保存
            result = {
                "working_arn": working_arn,
                "all_candidates": all_candidates,
                "test_timestamp": str(datetime.now())
            }
            
            with open("claude4_arn_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"💾 結果をclaude4_arn_result.jsonに保存しました")
        else:
            print(f"❌ BedrockClient更新に失敗しました")
    else:
        print(f"\n❌ 動作するClaude 4 ARNが見つかりませんでした")
        print(f"🔧 手動でAWS Bedrockコンソールを確認してください")
        print(f"📋 候補ARN一覧:")
        for candidate in all_candidates:
            print(f"   - {candidate['arn']}")

if __name__ == "__main__":
    from datetime import datetime
    main() 