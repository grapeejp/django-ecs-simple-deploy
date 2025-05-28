#!/usr/bin/env python3
"""
AWS Bedrock Claude 4 アクセステストスクリプト
校正AIアプリのClaude 4接続問題を診断・解決するためのテストツール
"""

import boto3
import json
import os
import sys
import traceback
from typing import Dict, Any, List
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bedrock_test.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class BedrockClaude4Tester:
    """AWS Bedrock Claude 4 接続テスター"""
    
    def __init__(self):
        """テスターの初期化"""
        self.region = os.environ.get("AWS_REGION", "ap-northeast-1")
        self.bedrock_runtime = None
        self.bedrock = None
        
        # テスト対象のモデルID
        self.claude4_models = [
            "apac.anthropic.claude-sonnet-4-20250514-v1:0",  # 現在使用中
            "anthropic.claude-3-5-sonnet-20241022-v2:0",     # フォールバック候補
            "anthropic.claude-3-5-sonnet-20240620-v1:0",     # 安定版
            "anthropic.claude-3-sonnet-20240229-v1:0"        # 旧版
        ]
        
    def test_aws_credentials(self) -> bool:
        """AWS認証情報のテスト"""
        logger.info("🔑 AWS認証情報テスト開始")
        
        try:
            # STS経由でアイデンティティ確認
            sts = boto3.client('sts', region_name=self.region)
            identity = sts.get_caller_identity()
            
            logger.info("✅ AWS認証情報: 正常")
            logger.info(f"   - Account ID: {identity.get('Account')}")
            logger.info(f"   - User ID: {identity.get('UserId')}")
            logger.info(f"   - ARN: {identity.get('Arn')}")
            logger.info(f"   - Region: {self.region}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ AWS認証情報エラー: {str(e)}")
            logger.error(f"📋 スタックトレース:\n{traceback.format_exc()}")
            return False
    
    def test_bedrock_service_access(self) -> bool:
        """Bedrockサービスアクセステスト"""
        logger.info("🔧 Bedrockサービスアクセステスト開始")
        
        try:
            # Bedrockクライアント作成
            self.bedrock = boto3.client('bedrock', region_name=self.region)
            self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=self.region)
            
            logger.info("✅ Bedrockクライアント作成: 成功")
            
            # 基本的なサービス接続テスト
            try:
                # Foundation Modelsの一覧取得を試行
                response = self.bedrock.list_foundation_models()
                models = response.get('modelSummaries', [])
                logger.info(f"✅ Foundation Models取得: 成功 ({len(models)}モデル)")
                
                # Claude関連モデルの確認
                claude_models = [m for m in models if 'claude' in m.get('modelId', '').lower()]
                logger.info(f"🤖 Claude関連モデル数: {len(claude_models)}")
                
                for model in claude_models[:10]:  # 最初の10個を表示
                    logger.info(f"   - {model.get('modelId')} ({model.get('modelName', 'N/A')})")
                
                return True
                
            except Exception as list_error:
                logger.warning(f"⚠️ Foundation Models一覧取得エラー: {str(list_error)}")
                # 一覧取得に失敗してもランタイムは使える可能性がある
                return True
                
        except Exception as e:
            logger.error(f"❌ Bedrockサービスアクセスエラー: {str(e)}")
            logger.error(f"📋 スタックトレース:\n{traceback.format_exc()}")
            return False
    
    def test_model_access(self, model_id: str) -> Dict[str, Any]:
        """特定モデルのアクセステスト"""
        logger.info(f"🎯 モデルアクセステスト: {model_id}")
        
        result = {
            "model_id": model_id,
            "accessible": False,
            "error": None,
            "response_time": None,
            "test_response": None
        }
        
        try:
            import time
            start_time = time.time()
            
            # 簡単なテストプロンプト
            test_prompt = "こんにちは。簡単なテストです。「はい」と答えてください。"
            
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": test_prompt}]
                    }
                ]
            }
            
            body = json.dumps(payload)
            
            # モデル呼び出し
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=body
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
            
            result.update({
                "accessible": True,
                "response_time": response_time,
                "test_response": test_response,
                "usage": response_body.get("usage", {})
            })
            
            logger.info(f"✅ {model_id}: アクセス成功")
            logger.info(f"   - 応答時間: {response_time:.2f}秒")
            logger.info(f"   - テスト応答: {test_response[:100]}...")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ {model_id}: アクセス失敗")
            logger.error(f"   - エラー: {str(e)}")
            
            # エラータイプ別の詳細分析
            if 'AccessDenied' in str(e):
                logger.error("   - 原因: アクセス権限不足")
                logger.error("   - 対策: IAMポリシーでbedrock:InvokeModelの権限を追加")
            elif 'ValidationException' in str(e):
                logger.error("   - 原因: リクエスト形式またはモデルID不正")
                logger.error("   - 対策: モデルIDとペイロード形式を確認")
            elif 'ResourceNotFound' in str(e):
                logger.error("   - 原因: モデルが存在しないまたは利用不可")
                logger.error("   - 対策: 利用可能なモデル一覧を確認")
        
        return result
    
    def test_all_claude_models(self) -> List[Dict[str, Any]]:
        """全Claude モデルのアクセステスト"""
        logger.info("🚀 全Claudeモデルアクセステスト開始")
        
        results = []
        for model_id in self.claude4_models:
            result = self.test_model_access(model_id)
            results.append(result)
        
        # 結果サマリー
        accessible_models = [r for r in results if r["accessible"]]
        logger.info(f"📊 テスト結果サマリー:")
        logger.info(f"   - テスト対象: {len(results)}モデル")
        logger.info(f"   - アクセス可能: {len(accessible_models)}モデル")
        logger.info(f"   - アクセス不可: {len(results) - len(accessible_models)}モデル")
        
        if accessible_models:
            logger.info("✅ アクセス可能なモデル:")
            for model in accessible_models:
                logger.info(f"   - {model['model_id']} (応答時間: {model['response_time']:.2f}秒)")
        
        return results
    
    def check_iam_permissions(self) -> Dict[str, Any]:
        """IAM権限の確認"""
        logger.info("🔐 IAM権限確認開始")
        
        permissions_check = {
            "bedrock_access": False,
            "bedrock_runtime_access": False,
            "specific_errors": []
        }
        
        try:
            # Bedrock基本アクセス確認
            try:
                self.bedrock.list_foundation_models()
                permissions_check["bedrock_access"] = True
                logger.info("✅ bedrock:ListFoundationModels: 権限あり")
            except Exception as e:
                permissions_check["specific_errors"].append(f"bedrock:ListFoundationModels: {str(e)}")
                logger.warning(f"⚠️ bedrock:ListFoundationModels: 権限なし - {str(e)}")
            
            # Bedrock Runtime アクセス確認（簡単なモデル呼び出し）
            try:
                # 最もアクセスしやすいモデルでテスト
                test_model = "anthropic.claude-3-sonnet-20240229-v1:0"
                payload = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": [{"type": "text", "text": "test"}]}]
                }
                
                self.bedrock_runtime.invoke_model(
                    modelId=test_model,
                    body=json.dumps(payload)
                )
                permissions_check["bedrock_runtime_access"] = True
                logger.info("✅ bedrock-runtime:InvokeModel: 権限あり")
                
            except Exception as e:
                permissions_check["specific_errors"].append(f"bedrock-runtime:InvokeModel: {str(e)}")
                logger.warning(f"⚠️ bedrock-runtime:InvokeModel: 権限なし - {str(e)}")
        
        except Exception as e:
            logger.error(f"❌ IAM権限確認エラー: {str(e)}")
            permissions_check["specific_errors"].append(f"General IAM check: {str(e)}")
        
        return permissions_check
    
    def generate_iam_policy_recommendation(self, test_results: List[Dict[str, Any]]) -> str:
        """テスト結果に基づくIAMポリシー推奨事項の生成"""
        logger.info("📋 IAMポリシー推奨事項生成")
        
        accessible_models = [r["model_id"] for r in test_results if r["accessible"]]
        failed_models = [r for r in test_results if not r["accessible"]]
        
        policy_recommendation = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:ListFoundationModels",
                        "bedrock:GetFoundationModel",
                        "bedrock:InvokeModel"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-runtime:InvokeModel",
                        "bedrock-runtime:InvokeModelWithResponseStream"
                    ],
                    "Resource": [
                        f"arn:aws:bedrock:{self.region}::foundation-model/{model_id}"
                        for model_id in self.claude4_models
                    ]
                }
            ]
        }
        
        policy_json = json.dumps(policy_recommendation, indent=2, ensure_ascii=False)
        
        logger.info("📄 推奨IAMポリシー:")
        logger.info(policy_json)
        
        # ファイルに保存
        with open("recommended_bedrock_policy.json", "w", encoding="utf-8") as f:
            f.write(policy_json)
        
        logger.info("💾 推奨ポリシーをrecommended_bedrock_policy.jsonに保存しました")
        
        return policy_json
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """包括的なテストの実行"""
        logger.info("🚀 AWS Bedrock Claude 4 包括的テスト開始")
        logger.info("=" * 60)
        
        test_results = {
            "aws_credentials": False,
            "bedrock_service": False,
            "model_access_results": [],
            "iam_permissions": {},
            "recommendations": []
        }
        
        # 1. AWS認証情報テスト
        test_results["aws_credentials"] = self.test_aws_credentials()
        if not test_results["aws_credentials"]:
            logger.error("❌ AWS認証情報に問題があります。テストを中断します。")
            return test_results
        
        # 2. Bedrockサービスアクセステスト
        test_results["bedrock_service"] = self.test_bedrock_service_access()
        if not test_results["bedrock_service"]:
            logger.error("❌ Bedrockサービスにアクセスできません。テストを中断します。")
            return test_results
        
        # 3. 全Claudeモデルアクセステスト
        test_results["model_access_results"] = self.test_all_claude_models()
        
        # 4. IAM権限確認
        test_results["iam_permissions"] = self.check_iam_permissions()
        
        # 5. 推奨事項生成
        accessible_models = [r for r in test_results["model_access_results"] if r["accessible"]]
        
        if accessible_models:
            test_results["recommendations"].append("✅ 利用可能なモデルが見つかりました")
            best_model = min(accessible_models, key=lambda x: x["response_time"])
            test_results["recommendations"].append(f"🎯 推奨モデル: {best_model['model_id']} (応答時間: {best_model['response_time']:.2f}秒)")
        else:
            test_results["recommendations"].append("❌ 利用可能なモデルがありません")
            test_results["recommendations"].append("🔧 IAMポリシーの確認・更新が必要です")
        
        # 6. IAMポリシー推奨事項生成
        self.generate_iam_policy_recommendation(test_results["model_access_results"])
        
        # 最終結果サマリー
        logger.info("=" * 60)
        logger.info("📊 最終テスト結果サマリー")
        logger.info("=" * 60)
        logger.info(f"AWS認証情報: {'✅ 正常' if test_results['aws_credentials'] else '❌ 異常'}")
        logger.info(f"Bedrockサービス: {'✅ 正常' if test_results['bedrock_service'] else '❌ 異常'}")
        logger.info(f"アクセス可能モデル数: {len(accessible_models)}/{len(test_results['model_access_results'])}")
        
        logger.info("\n📋 推奨事項:")
        for rec in test_results["recommendations"]:
            logger.info(f"   {rec}")
        
        return test_results

def main():
    """メイン実行関数"""
    print("🚀 AWS Bedrock Claude 4 アクセステスト開始")
    print("=" * 60)
    
    try:
        tester = BedrockClaude4Tester()
        results = tester.run_comprehensive_test()
        
        # 結果をJSONファイルに保存
        with open("bedrock_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print("\n💾 テスト結果をbedrock_test_results.jsonに保存しました")
        print("📄 ログはbedrock_test.logに保存されました")
        print("📋 推奨IAMポリシーはrecommended_bedrock_policy.jsonに保存されました")
        
        # 成功した場合の次のステップ
        accessible_models = [r for r in results["model_access_results"] if r["accessible"]]
        if accessible_models:
            print(f"\n✅ {len(accessible_models)}個のモデルにアクセス可能です")
            print("🔧 校正AIアプリの設定を更新してください")
        else:
            print("\n❌ アクセス可能なモデルがありません")
            print("🔧 IAMポリシーを確認・更新してください")
        
    except Exception as e:
        logger.error(f"❌ テスト実行エラー: {str(e)}")
        logger.error(f"📋 スタックトレース:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main() 