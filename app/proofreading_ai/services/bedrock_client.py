import boto3
import json
import os
import time
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class BedrockClient:
    """AWS Bedrockサービスのクライアントクラス"""
    
    def __init__(self):
        """
        Bedrockクライアントの初期化
        """
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
        )
        # Claude 3 Sonnetモデル
        self.model_id = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
        
        # プロンプトファイルのパスを設定
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.prompt_path = os.environ.get(
            "BEDROCK_PROMPT_PATH", 
            os.path.join(base_dir, "prompt.md")
        )
        
        # デフォルトプロンプトの読み込み
        try:
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                self.default_prompt = f.read()
        except FileNotFoundError:
            logger.warning(f"プロンプトファイルが見つかりません: {self.prompt_path}")
            self.default_prompt = "以下の文章を校正してください。"
    
    def proofread_text(self, text: str) -> Tuple[str, float]:
        """
        テキストを校正する
        
        Args:
            text: 校正する原文
            
        Returns:
            校正されたテキストと処理時間のタプル
        """
        start_time = time.time()
        
        prompt = f"{self.default_prompt}\n\n{text}"
        
        try:
            # Claude 3 Sonnetリクエスト
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            body = json.dumps(payload)
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            response_body = json.loads(response.get("body").read())
            corrected_text = response_body.get("content")[0].get("text", "")
            
            end_time = time.time()
            completion_time = end_time - start_time
            
            return corrected_text, completion_time
            
        except Exception as e:
            logger.error(f"Bedrock APIエラー: {str(e)}")
            raise e

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