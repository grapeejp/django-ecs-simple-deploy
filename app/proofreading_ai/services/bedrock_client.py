import boto3
from botocore.config import Config
import json
import os
import time
from typing import Dict, Any, Tuple, List
import logging
import re
import traceback
from proofreading_ai.utils import protect_html_tags_advanced, restore_html_tags_advanced

# チャットワーク通知サービスをインポート
try:
    from proofreading_ai.services.notification_service import ChatworkNotificationService
    CHATWORK_AVAILABLE = True
except ImportError:
    CHATWORK_AVAILABLE = False
    ChatworkNotificationService = None

logger = logging.getLogger(__name__)

class BedrockClient:
    """AWS Bedrockサービスのクライアントクラス - Claude Sonnet 4 アプリケーション推論プロファイル対応"""
    
    def __init__(self):
        """
        Bedrockクライアントの初期化（詳細デバッグ対応）
        """
        try:
            logger.info("🔧 BedrockClient初期化開始")
            
            # AWS設定の確認
            aws_region = os.environ.get("AWS_REGION", "ap-northeast-1")
            logger.info(f"🌏 AWSリージョン: {aws_region}")
            
            # AWS認証情報の確認
            try:
                import boto3
                session = boto3.Session()
                credentials = session.get_credentials()
                if credentials:
                    logger.info(f"🔑 AWS認証情報: 利用可能")
                    logger.info(f"   - アクセスキーID: {credentials.access_key[:8]}...")
                    logger.info(f"   - トークン: {'あり' if credentials.token else 'なし'}")
                else:
                    logger.warning("⚠️ AWS認証情報が見つかりません")
            except Exception as cred_error:
                logger.warning(f"⚠️ AWS認証情報確認エラー: {str(cred_error)}")
            
            # Claude 4対応のタイムアウト設定
            # 長時間処理に対応するため大幅に延長
            timeout_config = Config(
                read_timeout=600,     # 10分
                connect_timeout=60,   # 1分
                retries={'max_attempts': 3}
            )
            
            # Bedrockクライアントの作成
            self.bedrock_runtime = boto3.client(
                service_name="bedrock-runtime",
                region_name=aws_region,
                config=timeout_config
            )
            # コントロールプレーン用のBedrockクライアントも作成
            self.bedrock = boto3.client(
                service_name="bedrock",
                region_name=aws_region,
                config=timeout_config
            )
            logger.info(f"✅ Bedrockランタイムクライアント作成完了")
            
            # アプリケーション推論プロファイル使用（校正AI専用）
            # コスト追跡とメトリクス監視が可能
            # Claude Sonnet 4を使用（正しいモデルID）
            # Claude Sonnet 4 推論プロファイルARN（発見済み）
            # アクセス権限申請中 - 承認後に利用可能
            self.model_id = "arn:aws:bedrock:ap-northeast-1:026090540679:inference-profile/apac.anthropic.claude-sonnet-4-20250514-v1:0"
            
            # フォールバック: Claude 3.5 Sonnet（動作確認済み）
            self.fallback_model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
            
            logger.info(f"🎯 プライマリモデル: {self.model_id}")
            logger.info(f"🔄 フォールバックモデル: {self.fallback_model_id}")
            
            # モデルアクセス権限の事前確認
            try:
                logger.info("🔍 モデルアクセス権限確認開始")
                self._check_model_access()
                logger.info("✅ モデルアクセス権限確認完了")
            except Exception as access_error:
                logger.warning(f"⚠️ モデルアクセス権限確認エラー: {str(access_error)}")
            
            # トークンあたりの価格設定（Claude Sonnet 4）
            self.input_price_per_1k_tokens = float(os.environ.get("INPUT_PRICE_PER_1K_TOKENS", 0.003))
            self.output_price_per_1k_tokens = float(os.environ.get("OUTPUT_PRICE_PER_1K_TOKENS", 0.015))
            self.yen_per_dollar = float(os.environ.get("YEN_PER_DOLLAR", 150))
            
            logger.info(f"💰 価格設定:")
            logger.info(f"   - 入力: ${self.input_price_per_1k_tokens}/1000トークン")
            logger.info(f"   - 出力: ${self.output_price_per_1k_tokens}/1000トークン")
            logger.info(f"   - 為替レート: {self.yen_per_dollar}円/USD")
            
            # アプリケーション推論プロファイル情報
            self.profile_info = {
                "name": "proofreading-ai-claude-sonnet-4",
                "description": "校正AI専用Claude Sonnet 4プロファイル",
                "tags": {
                    "Application": "ProofreadingAI",
                    "Environment": "Production",
                    "Team": "AI-Development",
                    "Model": "Claude-Sonnet-4"
                }
            }
            
            logger.info(f"📊 プロファイル情報: {self.profile_info['name']}")
            
            # API タイムアウト設定
            self.api_timeout = int(os.environ.get("BEDROCK_API_TIMEOUT", 300))  # デフォルト5分
            logger.info(f"⏰ APIタイムアウト: {self.api_timeout}秒")
            
            # プロンプトファイルのパスを設定
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.prompt_path = os.environ.get(
                "BEDROCK_PROMPT_PATH", 
                os.path.join(base_dir, "prompt.md")
            )
            
            logger.info(f"📄 プロンプトファイルパス: {self.prompt_path}")
            
            # デフォルトプロンプトの読み込み
            try:
                with open(self.prompt_path, "r", encoding="utf-8") as f:
                    self.default_prompt = f.read()
                logger.info(f"✅ プロンプトファイル読み込み成功: {len(self.default_prompt)}文字")
            except FileNotFoundError:
                logger.warning(f"⚠️ プロンプトファイルが見つかりません: {self.prompt_path}")
                self.default_prompt = self._get_default_prompt()
                logger.info(f"✅ デフォルトプロンプト使用: {len(self.default_prompt)}文字")
                
            logger.info("🎉 BedrockClient初期化完了")
            
        except Exception as e:
            logger.error(f"❌ BedrockClient初期化エラー: {str(e)}")
            logger.error(f"🔍 エラータイプ: {type(e).__name__}")
            import traceback
            logger.error(f"📋 スタックトレース:\n{traceback.format_exc()}")
            
            # チャットワーク通知送信
            if CHATWORK_AVAILABLE and ChatworkNotificationService:
                try:
                    chatwork_service = ChatworkNotificationService()
                    if chatwork_service.is_configured():
                        context = {
                            "function_name": "BedrockClient.__init__",
                            "error_type": type(e).__name__,
                            "aws_region": os.environ.get("AWS_REGION", "ap-northeast-1"),
                        }
                        chatwork_service.send_error_notification(
                            "BEDROCK_INIT_ERROR",
                            f"BedrockClient初期化に失敗しました: {str(e)}",
                            context
                        )
                except Exception as notification_error:
                    logger.error(f"📤 チャットワーク通知送信エラー: {str(notification_error)}")
            
            raise e

    def _check_model_access(self):
        """
        モデルアクセス権限を事前確認する
        """
        try:
            # 利用可能なモデル一覧を取得してアクセス権限を確認
            # BedrockRuntime ではなく Bedrock クライアントを使用
            response = self.bedrock.list_foundation_models()
            available_models = [model['modelId'] for model in response.get('modelSummaries', [])]
            
            logger.info(f"📋 利用可能なモデル数: {len(available_models)}")
            
            # Claude関連モデルの確認
            claude_models = [model for model in available_models if 'claude' in model.lower()]
            logger.info(f"🤖 Claude関連モデル数: {len(claude_models)}")
            
            for model in claude_models[:5]:  # 最初の5つだけログ出力
                logger.info(f"   - {model}")
                
        except Exception as e:
            logger.warning(f"⚠️ モデル一覧取得エラー: {str(e)}")
            
            # IAMアイデンティティの確認
            try:
                import boto3
                sts = boto3.client('sts')
                identity = sts.get_caller_identity()
                logger.info(f"🆔 現在のIAMアイデンティティ:")
                logger.info(f"   - Account: {identity.get('Account', '不明')}")
                logger.info(f"   - UserId: {identity.get('UserId', '不明')}")
                logger.info(f"   - Arn: {identity.get('Arn', '不明')}")
            except Exception as sts_error:
                logger.error(f"❌ IAMアイデンティティ取得エラー: {str(sts_error)}")
            
            # エラーを再発生させる代わりに、警告ログのみ出力
            logger.warning("⚠️ モデルアクセス権限確認でエラーが発生しましたが、継続します")

    def _get_default_prompt(self) -> str:
        """
        Claude Sonnet 4の矛盾チェック機能を強化したプロンプト（簡潔版）
        """
        return """あなたは日本語校正の専門家です。以下のカテゴリーで文章を校正してください。

**🟠 矛盾チェック（inconsistency）を必ず実行してください：**
- 地理的矛盾：「富士山は東京都大阪市にある」→「富士山は静岡県・山梨県境にある」
- 行政区分：「神奈川県横浜県」→「神奈川県横浜市」
- 番組放送局：「サザエさん（日本テレビ）」→「サザエさん（フジテレビ）」
- 学校年次：「小学8年生」→「小学6年生」
- 年齢矛盾：「今年25歳、去年27歳」→年齢逆転の指摘

**校正カテゴリー：**
1. 🟠 矛盾チェック（inconsistency）：論理的・事実的矛盾
2. 🔴 誤字修正（typo）：明確な誤字脱字（HTMLタグ内含む）
3. 🟡 社内辞書ルール（dict）：アマゾン→Amazon、大谷→大谷翔平など
4. 🟣 言い回しアドバイス（tone）：より自然な表現への改善

**重要：矛盾を発見した場合は必ず「inconsistency」カテゴリーで報告してください。**"""

    def _get_simple_prompt(self) -> str:
        """
        高速処理用のシンプルプロンプト（思考プロセス除去版）
        """
        return """あなたは日本語校正の専門家です。以下の文章を素早く校正してください。

校正カテゴリー：
1. 🟣 言い回しアドバイス（expression）：より自然で温かみのある表現への改善
2. 🔴 誤字修正（typo）：明確な誤字脱字の修正（HTMLタグ内も含む）
3. 🟡 社内辞書ルール（dictionary）：統一表記ルールの適用
4. 🟠 矛盾チェック（contradiction）：論理的・事実的矛盾の検出

校正対象：{原文}

修正後の文章をそのまま出力し、その後に修正箇所一覧を以下の形式で記載してください：

✅修正箇所：
- 行番号: (修正前) -> (修正後): 理由 [カテゴリー: tone|typo|dict|contradiction]"""

    def count_tokens(self, text: str) -> int:
        """
        トークン数を概算する簡易的な方法
        実際のトークン化アルゴリズムとは異なる場合があります
        
        Args:
            text: トークン数を計算するテキスト
            
        Returns:
            概算トークン数
        """
        # 日本語は文字あたり約1.5トークンと概算
        return int(len(text) * 1.5)
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        コストを計算する
        
        Args:
            input_tokens: 入力トークン数
            output_tokens: 出力トークン数
            
        Returns:
            日本円でのコスト
        """
        input_cost = (input_tokens / 1000) * self.input_price_per_1k_tokens
        output_cost = (output_tokens / 1000) * self.output_price_per_1k_tokens
        return (input_cost + output_cost) * self.yen_per_dollar
    
    def proofread_text(self, text: str, use_json_mode: bool = True, use_simple_prompt: bool = False) -> Dict:
        """
        テキストの校正を実行
        
        Args:
            text: 校正対象のテキスト
            use_json_mode: JSONモード（Tool Use）を使用するか
            use_simple_prompt: シンプルプロンプト（高速処理）を使用するか
            
        Returns:
            校正結果の辞書
        """
        logger.info(f"校正開始 - 文字数: {len(text)}文字, JSONモード: {use_json_mode}, シンプルプロンプト: {use_simple_prompt}")
        
        if use_json_mode:
            return self._proofread_with_json_mode(text, use_simple_prompt)
        else:
            return self._proofread_with_text_mode(text, use_simple_prompt)
    
    def _proofread_with_json_mode(self, text: str, use_simple_prompt: bool = False) -> Dict:
        """
        JSONモード（Tool Use）で校正を実行
        """
        try:
            # HTMLタグ保護
            protected_text, placeholders, html_tag_info = protect_html_tags_advanced(text)
            
            # プロンプト選択
            if use_simple_prompt:
                prompt = self._get_simple_prompt().replace("{原文}", protected_text)
                logger.info("🚀 高速処理モード: シンプルプロンプト使用")
            else:
                prompt = self.default_prompt.replace("{原文}", protected_text)
                logger.info("🎯 標準処理モード: デフォルトプロンプト使用")
            
            # Tool Use設定
            tools = [{
                "name": "proofreading_result",
                "description": "校正結果をJSON形式で出力するツール",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "corrected_text": {
                            "type": "string",
                            "description": "校正後のHTML込みテキスト全文"
                        },
                        "corrections": {
                            "type": "array",
                            "description": "修正箇所のリスト",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "line_number": {
                                        "type": "integer",
                                        "description": "修正箇所の行番号"
                                    },
                                    "original": {
                                        "type": "string",
                                        "description": "修正前のテキスト"
                                    },
                                    "corrected": {
                                        "type": "string",
                                        "description": "修正後のテキスト"
                                    },
                                    "reason": {
                                        "type": "string",
                                        "description": "修正理由の説明"
                                    },
                                    "category": {
                                        "type": "string",
                                        "enum": ["tone", "typo", "dict", "inconsistency"],
                                        "description": "修正カテゴリー: tone=言い回し, typo=誤字修正, dict=辞書ルール, inconsistency=矛盾チェック"
                                    }
                                },
                                "required": ["line_number", "original", "corrected", "reason", "category"]
                            }
                        }
                    },
                    "required": ["corrected_text", "corrections"]
                }
            }]
            
            # APIリクエストボディ
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 15000,  # JSON出力では少し多めに
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "tools": tools,
                "tool_choice": {"type": "tool", "name": "proofreading_result"}
            }
            
            # API呼び出し
            logger.info("AWS Bedrock API呼び出し開始（JSON Mode）")
            start_time = time.time()
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            logger.info(f"AWS Bedrock API呼び出し完了 - 処理時間: {processing_time:.2f}秒")
            
            # レスポンス解析
            response_body = json.loads(response["body"].read())
            logger.info(f"APIレスポンス: {json.dumps(response_body, ensure_ascii=False, indent=2)}")
            
            # Tool Use結果の抽出
            if "content" not in response_body or not response_body["content"]:
                raise ValueError("APIレスポンスにcontentが含まれていません")
            
            tool_use_content = None
            for content_block in response_body["content"]:
                if content_block.get("type") == "tool_use":
                    tool_use_content = content_block.get("input", {})
                    break
            
            if not tool_use_content:
                raise ValueError("Tool Useの結果が見つかりません")
            
            # HTMLタグ復元
            corrected_text = tool_use_content.get("corrected_text", "")
            corrections = tool_use_content.get("corrections", [])
            
            # プレースホルダーからHTMLタグを復元（4つの引数を正しく渡す）
            final_text = restore_html_tags_advanced(corrected_text, placeholders, html_tag_info, corrections)
            
            return {
                "corrected_text": final_text,
                "corrections": corrections,
                "processing_time": processing_time,
                "original_length": len(text),
                "mode": "json"
            }
            
        except Exception as e:
            error_msg = f"校正処理中にエラーが発生しました: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return {
                "error": error_msg,
                "corrected_text": text,
                "corrections": [],
                "processing_time": 0,
                "mode": "json"
            }
    
    def _proofread_with_text_mode(self, text: str, use_simple_prompt: bool = False) -> Dict:
        """
        従来のテキストモードで校正を実行（後方互換性のため）
        """
        try:
            # HTMLタグ保護
            protected_text, placeholders, html_tag_info = protect_html_tags_advanced(text)
            
            # プロンプト選択
            if use_simple_prompt:
                prompt = self._get_simple_prompt().replace("{原文}", protected_text)
                logger.info("🚀 高速処理モード: シンプルプロンプト使用")
            else:
                prompt = self.default_prompt.replace("{原文}", protected_text)
                logger.info("🎯 標準処理モード: デフォルトプロンプト使用")
            
            # 通常のAPI呼び出し
            logger.info("AWS Bedrock API呼び出し開始（Text Mode）")
            start_time = time.time()
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,  # Claude 4のプライマリモデル使用
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 30000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }),
                contentType="application/json"
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # レスポンス解析
            response_body = json.loads(response["body"].read())
            corrected_text = ""
            
            if "content" in response_body:
                for content_block in response_body["content"]:
                    if content_block.get("type") == "text":
                        corrected_text += content_block.get("text", "")
            
            # HTMLタグ復元（4つの引数を正しく渡す）
            # まず修正箇所解析
            corrections = self._parse_corrections_from_response(corrected_text)
            final_text = restore_html_tags_advanced(corrected_text, placeholders, html_tag_info, corrections)
            
            return {
                "corrected_text": final_text,
                "corrections": corrections,
                "processing_time": processing_time,
                "original_length": len(text),
                "mode": "text"
            }
            
        except Exception as e:
            error_msg = f"校正処理中にエラーが発生しました: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return {
                "error": error_msg,
                "corrected_text": text,
                "corrections": [],
                "processing_time": 0,
                "mode": "text"
            }

    def _invoke_model_with_profile(self, full_prompt: str, input_tokens: int, temperature: float, top_p: float, start_time: float) -> Tuple[str, list, float, Dict]:
        """
        指定されたプロファイルでモデルを呼び出す（詳細デバッグ対応）
        
        Args:
            full_prompt: 完全なプロンプト
            input_tokens: 入力トークン数
            temperature: 生成の創造性
            top_p: 核サンプリング
            start_time: 開始時刻
            
        Returns:
            校正結果のタプル
        """
        logger.info(f"🎯 モデル呼び出し開始")
        logger.info(f"📋 使用モデル: {self.model_id}")
        logger.info(f"⚙️ パラメータ: temperature={temperature}, top_p={top_p}")
        logger.info(f"📏 入力トークン数: {input_tokens}")
        
        try:
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 30000,
                "temperature": temperature,
                "top_p": top_p,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": full_prompt}],
                    }
                ]
            }
            
            body = json.dumps(payload)
            logger.info(f"📤 リクエストペイロードサイズ: {len(body)}バイト")
            
            # モデル呼び出し実行
            logger.info(f"🚀 Bedrock API呼び出し実行: {self.model_id}")
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=body
            )
            logger.info(f"✅ Bedrock API呼び出し成功")
            
            # レスポンス解析
            response_body = json.loads(response.get("body").read())
            logger.info(f"📥 レスポンス受信完了")
            
            content = response_body.get("content", [])
            corrected_text = ""
            tool_uses = []
            for c in content:
                if c.get("type") == "text":
                    corrected_text += c.get("text", "")
                elif c.get("type") == "tool_use":
                    tool_uses.append(c)
            
            usage = response_body.get("usage", {})
            model = response_body.get("model", "")
            
            logger.info(f"📊 レスポンス解析結果:")
            logger.info(f"   - 生成テキスト長: {len(corrected_text)}文字")
            logger.info(f"   - ツール使用数: {len(tool_uses)}")
            logger.info(f"   - 使用情報: {usage}")
            logger.info(f"   - モデル情報: {model}")
            
            end_time = time.time()
            completion_time = end_time - start_time
            
            # 出力トークン数とコスト計算
            output_tokens = self.count_tokens(corrected_text)
            total_cost = self.calculate_cost(input_tokens, output_tokens)
            
            cost_info = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_cost": total_cost,
                "profile_type": "アプリケーション",
                "model_id": self.model_id,
                "profile_info": self.profile_info
            }
            
            logger.info(f"✅ モデル呼び出し完了")
            logger.info(f"📊 処理結果サマリー:")
            logger.info(f"   - 入力トークン: {input_tokens}")
            logger.info(f"   - 出力トークン: {output_tokens}")
            logger.info(f"   - 処理時間: {completion_time:.2f}秒")
            logger.info(f"   - 総コスト: {total_cost:.2f}円")
            logger.info(f"   - 使用モデル: {self.model_id}")
            
            # 修正箇所リストを解析
            corrections = self._parse_corrections_from_response(corrected_text)
            logger.info(f"📝 修正箇所解析結果: {len(corrections)}件")
            
            # デバッグ用：Claude 4の完全なレスポンステキストをログ出力
            logger.info(f"🔍 Claude 4の完全なレスポンス:\n{corrected_text}")
            
            return corrected_text, corrections, completion_time, cost_info
            
        except Exception as e:
            error_message = str(e)
            error_type = type(e).__name__
            stack_trace = traceback.format_exc()
            processing_time = time.time() - start_time
            
            logger.error(f"❌ Bedrock API呼び出しエラー: {error_message}")
            logger.error(f"🔍 エラータイプ: {error_type}")
            logger.error(f"📋 スタックトレース:\n{stack_trace}")
            
            # Chatwork通知を送信
            if CHATWORK_AVAILABLE and ChatworkNotificationService:
                try:
                    chatwork_service = ChatworkNotificationService()
                    if chatwork_service.is_configured():
                        error_context = {
                            'function': 'BedrockClient._invoke_model_with_profile',
                            'model_id': self.model_id,
                            'error_type': error_type,
                            'temperature': temperature,
                            'top_p': top_p,
                            'input_tokens': input_tokens,
                            'processing_time': processing_time,
                            'payload_size': len(body) if 'body' in locals() else 0,
                            'stack_trace': stack_trace
                        }
                        
                        chatwork_service.send_error_notification(
                            error_type="BEDROCK_API_ERROR",
                            error_message=f"Bedrock API呼び出しでエラー: {error_message}",
                            context=error_context
                        )
                        logger.info("✅ Chatwork API エラー通知送信完了")
                except Exception as notification_error:
                    logger.error(f"❌ Chatwork API エラー通知送信失敗: {str(notification_error)}")
            
            raise e

    def _parse_corrections_from_response(self, response_text: str) -> List[Dict]:
        """
        Claude 4のレスポンスから修正箇所を解析する（行番号ベース形式対応）
        
        Args:
            response_text: Claude 4からのレスポンステキスト
            
        Returns:
            修正箇所のリスト
        """
        corrections = []
        
        try:
            # "✅修正箇所："以降の部分を抽出
            if "✅修正箇所：" in response_text:
                corrections_section = response_text.split("✅修正箇所：")[1]
                
                # 各行を解析
                lines = corrections_section.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    
                    # 新しい形式対応: - 行番号: (変更前) -> (変更後): 理由 [カテゴリー: tone|typo|dict|inconsistency]
                    if line.startswith('- ') and ': ' in line and '[カテゴリー:' in line:
                        try:
                            # 行番号部分を除去
                            content_part = line[2:]  # "- " を除去
                            
                            # カテゴリー部分を抽出
                            category_match = re.search(r'\[カテゴリー:\s*(tone|typo|dict|inconsistency)\]', content_part)
                            category = 'general'
                            if category_match:
                                category_raw = category_match.group(1)
                                # カテゴリー名をマッピング
                                category_mapping = {
                                    'tone': 'tone',
                                    'typo': 'typo', 
                                    'dict': 'dict',
                                    'inconsistency': 'inconsistency'
                                }
                                category = category_mapping.get(category_raw, 'general')
                                
                                # カテゴリー部分を除去
                                content_part = content_part[:category_match.start()].strip()
                            
                            # 変更前後と理由を抽出: "行番号: (変更前) -> (変更後): 理由"
                            if ' -> ' in content_part and ': ' in content_part:
                                # 最初の ": " で分割して行番号部分を除去
                                colon_parts = content_part.split(': ', 1)
                                if len(colon_parts) >= 2:
                                    change_and_reason = colon_parts[1]
                                    
                                    # 最後の ": " で理由を分離
                                    if ': ' in change_and_reason:
                                        last_colon_pos = change_and_reason.rfind(': ')
                                        before_after = change_and_reason[:last_colon_pos]
                                        reason = change_and_reason[last_colon_pos + 2:]
                                    else:
                                        before_after = change_and_reason
                                        reason = ""
                                    
                                    if ' -> ' in before_after:
                                        original, corrected = before_after.split(' -> ', 1)
                                        
                                        # 括弧、HTMLタグの<>、プレースホルダーなどを適切に処理
                                        original = original.strip('()').strip('<>').strip()
                                        corrected = corrected.strip('()').strip('<>').strip()
                                        
                                        # HTMLタグやプレースホルダーから実際の修正対象を抽出
                                        original_clean = self._extract_core_word(original)
                                        corrected_clean = self._extract_core_word(corrected)
                                        
                                        # 空でない場合のみ追加
                                        if original_clean and corrected_clean and original_clean != corrected_clean:
                                            corrections.append({
                                                'original': original_clean,
                                                'corrected': corrected_clean,
                                                'reason': reason.strip(),
                                                'category': category
                                            })
                                            
                                            logger.info(f"   解析成功 (新形式): {category} | {original_clean} -> {corrected_clean}")
                                        
                                        # 元の形式も保持（フォールバック用）
                                        if original != original_clean or corrected != corrected_clean:
                                            corrections.append({
                                                'original': original,
                                                'corrected': corrected,
                                                'reason': reason.strip(),
                                                'category': category
                                            })
                        
                        except Exception as parse_error:
                            logger.warning(f"⚠️ 新形式修正箇所解析エラー: {line} - {str(parse_error)}")
                            continue
                    
                    # 旧形式も継続サポート: - カテゴリー: tone | (変更前) -> (変更後): 理由
                    elif line.startswith('- カテゴリー:'):
                        try:
                            # カテゴリーを抽出
                            category_part = line.split('|')[0].replace('- カテゴリー:', '').strip()
                            
                            # 変更前後と理由を抽出
                            change_part = line.split('|')[1].strip()
                            if ' -> ' in change_part:
                                # 理由がある場合とない場合に対応
                                if ': ' in change_part:
                                    before_after, reason = change_part.split(': ', 1)
                                else:
                                    before_after = change_part
                                    reason = ""
                                
                                if ' -> ' in before_after:
                                    original, corrected = before_after.split(' -> ', 1)
                                    
                                    # 括弧、HTMLタグの<>、プレースホルダーなどを適切に処理
                                    original = original.strip('()').strip('<>').strip()
                                    corrected = corrected.strip('()').strip('<>').strip()
                                    
                                    # HTMLタグやプレースホルダーから実際の修正対象を抽出
                                    original_clean = self._extract_core_word(original)
                                    corrected_clean = self._extract_core_word(corrected)
                                    
                                    # 空でない場合のみ追加
                                    if original_clean and corrected_clean and original_clean != corrected_clean:
                                        corrections.append({
                                            'original': original_clean,
                                            'corrected': corrected_clean,
                                            'reason': reason.strip(),
                                            'category': category_part
                                        })
                                        
                                        logger.info(f"   解析成功 (旧形式): {category_part} | {original_clean} -> {corrected_clean}")
                                
                        except Exception as parse_error:
                            logger.warning(f"⚠️ 旧形式修正箇所解析エラー: {line} - {str(parse_error)}")
                            continue
            
            logger.info(f"📊 修正箇所解析完了: {len(corrections)}件")
            return corrections
            
        except Exception as e:
            logger.error(f"❌ 修正箇所解析エラー: {str(e)}")
            return []

    def _extract_core_word(self, text: str) -> str:
        """
        HTMLタグやプレースホルダーから核となる単語を抽出
        
        Args:
            text: 元のテキスト
            
        Returns:
            核となる単語
        """
        import re
        
        # プレースホルダーパターンから単語を抽出
        # 例: "__HTML_TAG_0__ dv __TAG_END_0__" → "dv"
        placeholder_match = re.search(r'__HTML_TAG_\d+__ (\w+) __TAG_', text)
        if placeholder_match:
            return placeholder_match.group(1)
        
        # HTMLタグから要素名を抽出
        # 例: "<dv>" → "dv", "</dv>" → "dv"
        html_tag_match = re.search(r'</?(\w+)[^>]*>', text)
        if html_tag_match:
            return html_tag_match.group(1)
        
        # 属性パターンを抽出
        # 例: 'clss="commnet"' → "clss" と "commnet" を両方抽出
        attr_matches = re.findall(r'(\w+)="?(\w+)"?', text)
        if attr_matches:
            # 最初のマッチから属性名を返す（通常は属性名の誤字が重要）
            return attr_matches[0][0]
        
        # 単純な単語を返す
        word_match = re.search(r'\b\w+\b', text)
        if word_match:
            return word_match.group(0)
        
        return text.strip()

    def apply_replacement_dictionary(self, text: str, replacements: Dict[str, str]) -> str:
        """
        置換辞書を適用してテキスト中の単語を置換する
        
        Args:
            text: 置換対象のテキスト
            replacements: キーが元の単語、値が置換後の単語の辞書
            
        Returns:
            置換後のテキスト
        """
        result = text
        for original, replacement in replacements.items():
            result = result.replace(original, replacement)
        return result 