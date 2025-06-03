import boto3
import json
import os
import time
from typing import Dict, Any, Tuple, List
import logging
import re
from proofreading_ai.utils import protect_html_tags_advanced, restore_html_tags_advanced

# チャットワーク通知サービスをインポート
try:
    from proofreading_ai.services.notification_service import chatwork_service
    CHATWORK_AVAILABLE = True
except ImportError:
    CHATWORK_AVAILABLE = False
    chatwork_service = None

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
            
            # Bedrockクライアントの作成
            self.bedrock_runtime = boto3.client(
                service_name="bedrock-runtime",
                region_name=aws_region,
            )
            # コントロールプレーン用のBedrockクライアントも作成
            self.bedrock = boto3.client(
                service_name="bedrock",
                region_name=aws_region,
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
            if CHATWORK_AVAILABLE and chatwork_service and chatwork_service.is_configured():
                try:
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
        Claude Sonnet 4の拡張思考機能を活用したデフォルトプロンプト（HTMLタグ内誤字検出対応）
        """
        return """あなたは日本語校正の専門家です。以下の文章を4つのカテゴリーで詳細に校正してください。

<thinking>
まず文章全体を読み、以下の観点で分析します：
1. 🟣 言い回しアドバイス：より自然で温かみのある表現への改善
2. 🔴 誤字修正：明確な誤字脱字の修正（HTMLタグ名や属性値内の誤字も含む）
3. 🟡 社内辞書ルール：統一表記ルールの適用
4. 🟠 矛盾チェック：論理的・事実的矛盾の検出

HTMLタグについては、基本構造は保持しつつ、以下の修正を行います：
- タグ名の誤字修正（例：<dv> → <div>）
- 属性値内の誤字修正（例：class="commnet" → class="comment"）
- 属性名の誤字修正（例：clas → class）
- HTMLの構造自体は保持

各修正について、なぜその修正が必要なのか理由を明確にします。
</thinking>

校正ルール：
- HTMLタグの基本構造を保持しつつ、タグ名・属性名・属性値内の誤字は修正する
- 文章全体を出力し、途中で切らない
- 各修正にカテゴリーを明確に分類
- 修正理由を具体的に説明

校正カテゴリー：
1. 🟣 言い回しアドバイス（tone）：より自然で温かみのある表現への改善
2. 🔴 誤字修正（typo）：明確な誤字脱字の修正（HTMLタグ内も含む）
3. 🟡 社内辞書ルール（dict）：統一表記ルールの適用
4. 🟠 矛盾チェック（inconsistency）：論理的・事実的矛盾の検出"""

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
    
    def proofread_text(self, text: str, replacement_dict: Dict[str, str] = None, temperature: float = 0.1, top_p: float = 0.7) -> Tuple[str, list, float, Dict]:
        """
        Claude Sonnet 4を使用してテキストを校正する（アプリケーション推論プロファイル対応）
        
        Args:
            text: 校正する原文
            replacement_dict: 置換辞書
            temperature: 生成の創造性（0.0-1.0）
            top_p: 核サンプリング（0.0-1.0）
            
        Returns:
            校正されたテキスト、修正箇所リスト（JSON）、処理時間、コスト情報のタプル
        """
        start_time = time.time()
        
        # ステップ1: HTMLタグを保護（advanced版）
        logger.info(f"🛡️ HTMLタグ保護処理開始")
        protected_text, placeholders, html_tag_info = protect_html_tags_advanced(text)
        logger.info(f"📋 保護されたHTMLタグ数: {len(placeholders)}")
        logger.info(f"🏷️ HTMLタグ詳細情報数: {len(html_tag_info)}")
        
        # 置換指示の準備
        replacement_instructions = ""
        if replacement_dict:
            replacement_instructions = f"""
            以下の置換ルールを参考にしてください。ただし、文脈に応じて適切な場合のみ置換を行ってください：
            {json.dumps(replacement_dict, ensure_ascii=False, indent=2)}
            """
        
        # Claude Sonnet 4の拡張思考機能を活用したプロンプト（保護されたテキストを使用）
        full_prompt = f"""{self.default_prompt}

        {replacement_instructions}

        原文:
        {protected_text}

        <thinking>
        この文章を4つのカテゴリーで分析します：

        1. 🟣 言い回しアドバイス（tone）：
           - より自然で読みやすい表現への改善
           - 温かみのある表現への修正
           - 文体の統一

        2. 🔴 誤字修正（typo）：
           - 明確な誤字脱字
           - 変換ミス
           - 送り仮名の間違い
           - HTMLタグ名の誤字（例：dv → div, sepn → span）
           - HTML属性名の誤字（例：clss → class）

        3. 🟡 社内辞書ルール（dict）：
           - 統一表記ルールの適用
           - 専門用語の統一
           - 表記ゆれの修正

        4. 🟠 矛盾チェック（inconsistency）：
           - 論理的矛盾
           - 事実的矛盾
           - 数値の不整合
           - 時系列の矛盾

        各修正について、カテゴリーと理由を明確にします。
        HTMLタグ名や属性名の修正も必ず「✅修正箇所：」セクションに含めてください。
        </thinking>

        校正後のテキストをHTML形式で出力してください。HTMLタグの基本構造を保持しつつ、タグ名・属性名・属性値内の誤字は修正してください。
        必ず文章全体を出力し、途中で切らないこと。

        重要：HTMLタグ名や属性名の修正も含めて、すべての修正を「✅修正箇所：」セクションに記載してください。

        出力形式：
        [校正後のテキスト全文]

        ✅修正箇所：
        - カテゴリー: tone | (変更前) -> (変更後): 理由
        - カテゴリー: typo | (変更前) -> (変更後): 理由  ← HTMLタグの修正もここに含める
        - カテゴリー: dict | (変更前) -> (変更後): 理由
        - カテゴリー: inconsistency | (変更前) -> (変更後): 理由
        """
        
        input_tokens = self.count_tokens(full_prompt)
        
        # Claude Sonnet 4での実行（フォールバック付き）
        try:
            logger.info(f"🎯 Claude Sonnet 4で実行: {self.model_id}")
            corrected_text, corrections, processing_time, cost_info = self._invoke_model_with_profile(full_prompt, input_tokens, temperature, top_p, start_time)
            
            # ステップ2: HTMLタグを復元（修正適用）
            logger.info(f"🔄 HTMLタグ復元処理開始")
            final_corrected_text = restore_html_tags_advanced(corrected_text, placeholders, html_tag_info, corrections)
            logger.info(f"✅ HTMLタグ復元完了")
            
            # デバッグ用：Claude 4の完全なレスポンステキストをログ出力
            logger.info(f"🔍 Claude 4の完全なレスポンス:\n{corrected_text}")
            
            return final_corrected_text, corrections, processing_time, cost_info
            
        except Exception as e:
            logger.error(f"❌ Claude Sonnet 4でエラー: {str(e)}")
            
            # フォールバックがある場合は試行
            if self.fallback_model_id:
                logger.info(f"🔄 フォールバックモデルで再試行: {self.fallback_model_id}")
                try:
                    # 一時的にモデルIDを変更
                    original_model_id = self.model_id
                    self.model_id = self.fallback_model_id
                    
                    # フォールバックモデルで実行
                    corrected_text, corrections, processing_time, cost_info = self._invoke_model_with_profile(full_prompt, input_tokens, temperature, top_p, start_time)
                    
                    # HTMLタグを復元（修正適用）
                    logger.info(f"🔄 フォールバック後HTMLタグ復元処理開始")
                    final_corrected_text = restore_html_tags_advanced(corrected_text, placeholders, html_tag_info, corrections)
                    logger.info(f"✅ フォールバック後HTMLタグ復元完了")
                    
                    # モデルIDを元に戻す
                    self.model_id = original_model_id
                    
                    # デバッグ用：Claude 4の完全なレスポンステキストをログ出力
                    logger.info(f"🔍 Claude 4の完全なレスポンス:\n{corrected_text}")
                    
                    return final_corrected_text, corrections, processing_time, cost_info
                    
                except Exception as fallback_error:
                    logger.error(f"❌ フォールバックモデルでもエラー: {str(fallback_error)}")
                    # モデルIDを元に戻す
                    self.model_id = original_model_id
                    raise fallback_error
            else:
                raise e

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
            logger.error(f"❌ モデル呼び出しエラー発生")
            logger.error(f"🔍 エラータイプ: {type(e).__name__}")
            logger.error(f"🔍 エラーメッセージ: {str(e)}")
            
            # 完全なスタックトレース
            import traceback
            logger.error(f"📋 完全なスタックトレース:\n{traceback.format_exc()}")
            
            # チャットワーク通知送信
            if CHATWORK_AVAILABLE and chatwork_service and chatwork_service.is_configured():
                try:
                    context = {
                        "function_name": "_invoke_model_with_profile",
                        "model_id": self.model_id,
                        "error_type": type(e).__name__,
                        "temperature": temperature,
                        "top_p": top_p,
                        "input_tokens": input_tokens
                    }
                    
                    # エラー種別に応じて詳細メッセージを作成
                    if 'AccessDenied' in str(e):
                        error_type = "MODEL_ACCESS_DENIED"
                        error_message = f"モデルアクセス拒否: {self.model_id}"
                    elif 'ValidationException' in str(e):
                        error_type = "MODEL_VALIDATION_ERROR"
                        error_message = f"モデルパラメータ検証エラー: {str(e)}"
                    elif 'ThrottlingException' in str(e):
                        error_type = "MODEL_THROTTLING_ERROR"
                        error_message = f"モデル呼び出し頻度制限: {str(e)}"
                    elif 'ServiceUnavailableException' in str(e):
                        error_type = "MODEL_SERVICE_UNAVAILABLE"
                        error_message = f"Bedrockサービス利用不可: {str(e)}"
                    else:
                        error_type = "MODEL_INVOKE_ERROR"
                        error_message = f"モデル呼び出しエラー: {str(e)}"
                    
                    chatwork_service.send_error_notification(
                        error_type,
                        error_message,
                        context
                    )
                except Exception as notification_error:
                    logger.error(f"📤 チャットワーク通知送信エラー: {str(notification_error)}")
            
            raise e

    def _parse_corrections_from_response(self, response_text: str) -> List[Dict]:
        """
        Claude 4のレスポンスから修正箇所を解析する（括弧なし形式対応）
        
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
                    if line.startswith('- カテゴリー:'):
                        # パターン: - カテゴリー: tone | (変更前) -> (変更後): 理由
                        # または: - カテゴリー: typo | <dv> -> <div> : 理由
                        # または: - カテゴリー: typo | clss="commnet" -> class="comment" : 理由
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
                                    # 例: "<dv>" → "dv", "__HTML_TAG_0__ dv __TAG_END_0__" → "dv"
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
                                        
                                        logger.info(f"   解析成功: {category_part} | {original_clean} -> {corrected_clean}")
                                    
                                    # HTMLタグ全体も保持（フォールバック用）
                                    if original != original_clean or corrected != corrected_clean:
                                        corrections.append({
                                            'original': original,
                                            'corrected': corrected,
                                            'reason': reason.strip(),
                                            'category': category_part
                                        })
                                        
                                        logger.info(f"   タグ全体保持: {category_part} | {original} -> {corrected}")
                                
                        except Exception as parse_error:
                            logger.warning(f"⚠️ 修正箇所解析エラー: {line} - {str(parse_error)}")
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