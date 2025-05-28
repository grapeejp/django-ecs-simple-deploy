# Claude Sonnet 4 アクセス権限設定手順

## 🎯 概要

Claude Sonnet 4は**アプリケーション推論プロファイル**として提供されており、通常のFoundation Modelとは異なる設定が必要です。

## 🔍 現在の状況

- **エラー**: `AccessDeniedException: You don't have access to the model with the specified model ID`
- **モデルID**: `apac.anthropic.claude-sonnet-4-20250514-v1:0`
- **リージョン**: `ap-northeast-1`

## 🛠️ 解決手順

### 1. AWS Bedrockコンソールでの確認

1. **AWS Bedrockコンソール**にアクセス
   ```
   https://ap-northeast-1.console.aws.amazon.com/bedrock/
   ```

2. **Model access**セクションを確認
   - 左メニューから「Model access」を選択
   - Claude Sonnet 4が利用可能かチェック

3. **Inference profiles**セクションを確認
   - 左メニューから「Inference profiles」を選択
   - アプリケーション推論プロファイルの状態を確認

### 2. Claude 4のアクセス申請

Claude 4は限定プレビューのため、アクセス申請が必要な場合があります：

1. **AWS Bedrockコンソール**で「Model access」→「Request model access」
2. **Claude Sonnet 4**を選択
3. **Use case**を記入：
   ```
   Japanese text proofreading application for business documents.
   Need Claude 4's advanced reasoning capabilities for high-quality corrections.
   ```
4. 申請を送信

### 3. IAMポリシーの更新

現在のポリシーに以下を追加：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:ap-northeast-1::foundation-model/apac.anthropic.claude-sonnet-4-20250514-v1:0",
                "arn:aws:bedrock:ap-northeast-1:026090540679:application-inference-profile/*",
                "arn:aws:bedrock:ap-northeast-1::inference-profile/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:ListFoundationModels",
                "bedrock:GetFoundationModel",
                "bedrock:ListInferenceProfiles",
                "bedrock:GetInferenceProfile",
                "bedrock:CreateApplicationInferenceProfile",
                "bedrock:DeleteApplicationInferenceProfile",
                "bedrock:GetApplicationInferenceProfile",
                "bedrock:ListApplicationInferenceProfiles"
            ],
            "Resource": "*"
        }
    ]
}
```

### 4. アプリケーション推論プロファイルの作成

Claude 4を使用するには、専用のアプリケーション推論プロファイルが必要な場合があります：

```bash
# AWS CLIでプロファイル作成
aws bedrock create-application-inference-profile \
    --inference-profile-name "proofreading-ai-claude-4" \
    --description "校正AI専用Claude 4プロファイル" \
    --model-source '{
        "copyFrom": "apac.anthropic.claude-sonnet-4-20250514-v1:0"
    }' \
    --tags Application=ProofreadingAI,Environment=Production \
    --region ap-northeast-1
```

### 5. 代替アプローチ：リージョン変更

Claude 4が`ap-northeast-1`で利用できない場合、他のリージョンを試す：

- `us-east-1` (バージニア北部)
- `us-west-2` (オレゴン)
- `eu-west-1` (アイルランド)

環境変数で変更：
```bash
export AWS_REGION=us-east-1
```

## 🧪 テスト方法

### 1. アクセス権限テスト
```bash
python test_bedrock_claude4.py
```

### 2. 利用可能なモデル確認
```bash
aws bedrock list-foundation-models --region ap-northeast-1 --output json | grep claude
```

### 3. 推論プロファイル確認
```bash
aws bedrock list-inference-profiles --region ap-northeast-1
```

## 🔄 フォールバック戦略

現在の設定では、Claude 4でエラーが発生した場合、自動的にClaude 3.5 Sonnetにフォールバックします：

1. **プライマリ**: Claude Sonnet 4 (`apac.anthropic.claude-sonnet-4-20250514-v1:0`)
2. **フォールバック**: Claude 3.5 Sonnet (`anthropic.claude-3-5-sonnet-20240620-v1:0`)

## 📞 サポート

Claude 4のアクセスに問題がある場合：

1. **AWS Support**にケースを作成
2. **Bedrock専用サポート**に連絡
3. **アカウントマネージャー**に相談

## 🎯 期待される結果

設定完了後：
- ✅ Claude 4での高品質校正
- ✅ 拡張思考機能の活用
- ✅ フォールバック機能による安定性
- ✅ コスト効率的な運用 