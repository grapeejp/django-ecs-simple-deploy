import json
import boto3
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class BedrockClient:
    """AWS Bedrock APIクライアント"""
    
    def __init__(self, region_name=None):
        """
        AWS Bedrock APIクライアントの初期化
        
        Args:
            region_name (str, optional): AWS リージョン名。デフォルトはNone（環境変数から取得）
        """
        self.region_name = region_name
        self.client = self._get_client()
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    def _get_client(self):
        """Bedrock Runtime クライアントを取得"""
        try:
            return boto3.client('bedrock-runtime', region_name=self.region_name)
        except ClientError as e:
            logger.error(f"AWS Bedrock クライアント作成エラー: {str(e)}")
            raise
    
    def invoke_model(self, prompt, max_tokens=4000, temperature=0.7):
        """
        Claude 3.7 Sonnetモデルを呼び出してレスポンスを取得
        
        Args:
            prompt (str): プロンプト文字列
            max_tokens (int, optional): 生成する最大トークン数。デフォルトは4000
            temperature (float, optional): 生成の温度パラメータ。デフォルトは0.7
            
        Returns:
            dict: モデルからのレスポンス
        """
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body
            
        except ClientError as e:
            logger.error(f"AWS Bedrock API呼び出しエラー: {str(e)}")
            raise
    
    def evaluate_grape_style(self, text, category, subcategory=None):
        """
        テキストのグレイプらしさを評価
        
        Args:
            text (str): 評価するテキスト
            category (str): カテゴリ名
            subcategory (str, optional): サブカテゴリ名
            
        Returns:
            dict: 評価結果
        """
        category_info = f"カテゴリ: {category}"
        if subcategory:
            category_info += f", サブカテゴリ: {subcategory}"
            
        prompt = f"""
        あなたはウェブメディア「grape（グレイプ）」の記事評価AIです。
        以下の記事テキストを分析し、グレイプらしさを0-100点で評価してください。
        {category_info}
        
        評価基準:
        1. 文体: 親しみやすさ、語尾表現、文の長さ（0-100点）
        2. 構成: 見出し使用、段落構成、質問形式の適切さ（0-100点）
        3. キーワード: カテゴリに適した用語・表現の使用（0-100点）
        
        総合評価と改善提案をJSON形式で返してください:
        ```
        {{
            "total_score": 数値,
            "writing_style_score": 数値,
            "structure_score": 数値,
            "keyword_score": 数値,
            "improvement_suggestions": "改善提案テキスト"
        }}
        ```
        
        評価するテキスト:
        {text}
        """
        
        response = self.invoke_model(prompt)
        
        # レスポンスからJSON結果を抽出
        try:
            content = response.get('content', [])
            text_content = next((block.get('text') for block in content if block.get('type') == 'text'), '')
            
            # JSON部分を抽出
            json_str = text_content.strip().split('```')[1].strip()
            if json_str.startswith('json'):
                json_str = json_str[4:].strip()
                
            result = json.loads(json_str)
            return result
            
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.error(f"レスポンス解析エラー: {str(e)}")
            logger.debug(f"生のレスポンス: {response}")
            raise ValueError("APIレスポンスの解析に失敗しました") 