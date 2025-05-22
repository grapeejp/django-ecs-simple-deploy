import boto3
import json
import os
import time
from typing import Dict, Any, Tuple, List
import logging
import re

logger = logging.getLogger(__name__)

class BedrockClient:
    """AWS Bedrockサービスのクライアントクラス"""
    
    def __init__(self):
        """
        Bedrockクライアントの初期化
        """
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=os.environ.get("AWS_REGION", "ap-northeast-1"),
        )
        # Claude 3.5 Sonnet v1（推論プロファイル不要）
        self.model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        
        # トークンあたりの価格設定
        self.input_price_per_1k_tokens = float(os.environ.get("INPUT_PRICE_PER_1K_TOKENS", 0.003))
        self.output_price_per_1k_tokens = float(os.environ.get("OUTPUT_PRICE_PER_1K_TOKENS", 0.015))
        self.yen_per_dollar = float(os.environ.get("YEN_PER_DOLLAR", 150))
        
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
    
    def proofread_text(self, text: str, replacement_dict: Dict[str, str] = None) -> Tuple[str, list, float, Dict]:
        """
        テキストを校正する
        
        Args:
            text: 校正する原文
            replacement_dict: 置換辞書
            
        Returns:
            校正されたテキスト、修正箇所リスト（JSON）、処理時間、コスト情報のタプル
        """
        start_time = time.time()
        
        # 置換指示の準備
        replacement_instructions = ""
        if replacement_dict:
            replacement_instructions = f"""
            以下の置換ルールを参考にしてください。ただし、文脈に応じて適切な場合のみ置換を行ってください：
            {json.dumps(replacement_dict, ensure_ascii=False, indent=2)}
            """
        
        # プロンプトの作成
        full_prompt = f"""
        {self.default_prompt}

        {replacement_instructions}

        原文:
        {text}

        置換後のテキストをHTML形式で出力してください。HTMLタグは絶対に変更せず、そのまま保持してください。
        必ず文章全体を出力し、途中で切らないこと
        テキストの内容のみを置換し、以下の形式で出力してください。先に置換したテキストを出してください。その後に修正箇所を出してください。：
        

        ✅修正箇所：
        - 行番号: (変更前) -> (変更後): 理由
        - 行番号: (変更前) -> (変更後): 理由
        ...
        """
        
        input_tokens = self.count_tokens(full_prompt)
        
        try:
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 30000,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": full_prompt}],
                    }
                ]
            }
            
            body = json.dumps(payload)
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            response_body = json.loads(response.get("body").read())
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
            
            end_time = time.time()
            completion_time = end_time - start_time
            
            # 出力トークン数とコスト計算
            output_tokens = self.count_tokens(corrected_text)
            total_cost = self.calculate_cost(input_tokens, output_tokens)
            
            cost_info = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_cost": total_cost
            }
            
            return corrected_text, tool_uses, usage, model, completion_time, cost_info
            
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