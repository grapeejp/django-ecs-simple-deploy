#!/usr/bin/env python3
"""
発見されたClaude 4 ARNテストスクリプト
"""

import boto3
import json
import time

def test_claude4_arn():
    """発見されたClaude 4 ARNをテスト"""
    
    # 発見されたClaude 4のARN
    claude4_arn = "arn:aws:bedrock:ap-northeast-1:026090540679:inference-profile/apac.anthropic.claude-sonnet-4-20250514-v1:0"
    
    print("🧪 Claude Sonnet 4 ARNテスト")
    print("=" * 50)
    print(f"🎯 テスト対象ARN: {claude4_arn}")
    
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-northeast-1')
        
        # テスト用ペイロード
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "こんにちは。簡単なテストです。「はい」と答えてください。"}]
                }
            ]
        }
        
        start_time = time.time()
        
        # モデル呼び出し
        response = bedrock_runtime.invoke_model(
            modelId=claude4_arn,
            body=json.dumps(payload)
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # レスポンス解析
        response_body = json.loads(response.get("body").read())
        content = response_body.get("content", [])
        
        test_response = ""
        for c in content:
            if c.get("type") == "text":
                test_response += c.get("text", "")
        
        print(f"✅ Claude Sonnet 4 テスト成功!")
        print(f"📝 応答: {test_response}")
        print(f"⏱️ 応答時間: {response_time:.2f}秒")
        print(f"📊 使用情報: {response_body.get('usage', {})}")
        
        # 校正テスト
        print(f"\n🔍 校正機能テスト")
        print("-" * 30)
        
        proofreading_payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": """あなたは日本語校正の専門家です。以下の文章を4つのカテゴリーで詳細に校正してください。

<thinking>
まず文章全体を読み、以下の観点で分析します：
1. 🟣 言い回しアドバイス：より自然で温かみのある表現への改善
2. 🔴 誤字修正：明確な誤字脱字の修正
3. 🟡 社内辞書ルール：統一表記ルールの適用
4. 🟠 矛盾チェック：論理的・事実的矛盾の検出

各修正について、なぜその修正が必要なのか理由を明確にします。
</thinking>

校正ルール：
- HTMLタグは絶対に変更せず、そのまま保持
- 文章全体を出力し、途中で切らない
- 各修正にカテゴリーを明確に分類
- 修正理由を具体的に説明

原文:
これは校正のテストです。いくつかの間違いが含まれています。こんにちわ。とても良いです。

校正後のテキストを出力してください。

出力形式：
[校正後のテキスト全文]

✅修正箇所：
- カテゴリー: tone | (変更前) -> (変更後): 理由
- カテゴリー: typo | (変更前) -> (変更後): 理由"""}]
                }
            ]
        }
        
        start_time = time.time()
        
        response = bedrock_runtime.invoke_model(
            modelId=claude4_arn,
            body=json.dumps(proofreading_payload)
        )
        
        end_time = time.time()
        proofreading_time = end_time - start_time
        
        response_body = json.loads(response.get("body").read())
        content = response_body.get("content", [])
        
        proofreading_response = ""
        for c in content:
            if c.get("type") == "text":
                proofreading_response += c.get("text", "")
        
        print(f"✅ 校正テスト成功!")
        print(f"⏱️ 校正時間: {proofreading_time:.2f}秒")
        print(f"📝 校正結果:")
        print(proofreading_response)
        print(f"📊 使用情報: {response_body.get('usage', {})}")
        
        return True, claude4_arn
        
    except Exception as e:
        print(f"❌ テスト失敗: {str(e)}")
        return False, None

def update_bedrock_client(working_arn):
    """BedrockClientを正しいARNで更新"""
    
    print(f"\n🔧 BedrockClient更新")
    print("=" * 30)
    
    try:
        import re
        
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
        print(f"🎯 新しいモデルID: {working_arn}")
        
        return True
        
    except Exception as e:
        print(f"❌ BedrockClient更新エラー: {str(e)}")
        return False

def main():
    """メイン実行"""
    
    print("🚀 Claude Sonnet 4 ARN最終テスト")
    print("=" * 60)
    
    # Claude 4 ARNテスト
    success, working_arn = test_claude4_arn()
    
    if success:
        # BedrockClient更新
        update_success = update_bedrock_client(working_arn)
        
        if update_success:
            print(f"\n🎉 Claude Sonnet 4設定完了!")
            print(f"🎯 使用ARN: {working_arn}")
            print(f"🚀 校正AIアプリでClaude Sonnet 4が使用可能になりました")
            
            # 結果保存
            result = {
                "success": True,
                "working_arn": working_arn,
                "test_timestamp": str(time.time())
            }
            
            with open("claude4_final_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"💾 結果をclaude4_final_result.jsonに保存しました")
        else:
            print(f"❌ BedrockClient更新に失敗しました")
    else:
        print(f"\n❌ Claude Sonnet 4のテストに失敗しました")

if __name__ == "__main__":
    main() 