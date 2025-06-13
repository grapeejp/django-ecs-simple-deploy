# AWS ECSへのDjangoデプロイ注意点

## アーキテクチャの違いによる問題

### 問題：アーキテクチャの不一致
- **開発環境**: M3チップ（ARM64アーキテクチャ）
- **本番環境**: AWS ECS（x86_64アーキテクチャ）
- **エラー例**: `exec /usr/local/bin/python: exec format error`

### 解決策
1. Dockerfileでプラットフォームを明示的に指定
   ```dockerfile
   FROM --platform=linux/amd64 python:3.9-slim
   ```

2. Docker buildコマンド実行時にもプラットフォームを指定
   ```bash
   docker build --platform=linux/amd64 -t your-image-name .
   ```

3. Docker Composeでビルドする場合
   ```yaml
   services:
     web:
       platform: linux/amd64
       build: .
   ```

## ECSでのDjangoデプロイにおける一般的な課題

### 1. 環境変数と設定管理
- ECSでの環境変数設定はタスク定義で行う必要がある
- 機密情報はAWS Secrets ManagerやSSMパラメータストアを使用する
- `settings.py`は環境変数から設定を読み込むように構成する

### 2. 静的ファイルの管理
- 静的ファイルはS3などに配置し、CloudFrontでCDN配信するのが望ましい
- `STATIC_ROOT`と`MEDIA_ROOT`の設定を確認

### 3. データベース接続
- RDSインスタンスとの接続設定（ホスト、ポート、認証情報）
- セキュリティグループの適切な設定が必要

### 4. ログ管理
- CloudWatchへのログ送信設定
- アプリケーションログとシステムログの分離

### 5. セキュリティ設定
- IAMロールの適切な権限設定
- セキュリティグループの制限
- ALBとACMによるHTTPS化

## デプロイを簡素化するためのベストプラクティス

### 1. インフラのコード化
- Terraformを使用してインフラをコード管理
- モジュール化して再利用性を高める

### 2. CI/CDパイプラインの構築
- GitHub ActionsやAWS CodePipelineでの自動デプロイ
- テスト→ビルド→デプロイの自動化

### 3. コンテナイメージの最適化
- マルチステージビルドを活用
- ベースイメージを軽量なものに変更（alpineなど）
- 不要なファイルをコピーしない

### 4. モニタリングの設定
- CloudWatchアラームの設定
- ヘルスチェックの適切な設定

## より簡単なデプロイ方法の検討

以下の代替手段もあります：

1. **AWS Elastic Beanstalk**
   - ECSよりも抽象度が高く、設定が簡易
   - Djangoのデプロイがより簡単に

2. **AWS App Runner**
   - コンテナ化されたウェブアプリケーションの簡易デプロイ
   - インフラ管理が不要

3. **AWS Amplify**
   - フルスタックアプリケーションの簡易デプロイ
   - CI/CDが組み込み済み

4. **サードパーティサービス**
   - Heroku, Render, Fly.ioなどのPaaSの利用

## デプロイチェックリスト

- [ ] Dockerfileにプラットフォーム指定が含まれているか
- [ ] ビルドコマンドでプラットフォームが指定されているか
- [ ] データベース接続設定は正しいか
- [ ] 静的ファイルの設定は適切か
- [ ] 環境変数は正しく設定されているか
- [ ] IAMロールに必要な権限があるか
- [ ] セキュリティグループは適切に設定されているか
- [ ] ヘルスチェックは動作するか
- [ ] ログ設定は適切か
- [ ] スケーリング設定は必要に応じて行われているか 

## ⚠️ 重要：デプロイ時の頻出ミス

### スタック名の勘違い（毎回発生する問題）
**問題**: デプロイスクリプトが想定するスタック名と実際のスタック名が異なる

**実際のスタック名**:
- クラスター: `django-ecs-cluster-staging-v2`
- サービス: `django-ecs-service-staging-simple`

**デプロイスクリプトが想定するスタック名**:
- クラスター: `django-ecs-cluster-staging`
- サービス: `django-ecs-service-staging`

**解決方法**:
1. 現在のスタック名を確認:
   ```bash
   aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --output json | jq '.StackSummaries[] | select(.StackName | contains("staging")) | {StackName: .StackName, StackStatus: .StackStatus}'
   ```

2. 正しいスタック名で手動更新:
   ```bash
   export AWS_ACCOUNT_ID=026090540679
   export AWS_REGION=ap-northeast-1
   IMAGE_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:latest"
   
   # 正しいスタック名で更新
   aws cloudformation update-stack \
     --stack-name django-ecs-service-staging-simple \
     --template-body file://cloudformation/ecs-service-staging-simple.yml \
     --parameters ParameterKey=ImageUrl,ParameterValue=$IMAGE_URL
   ```

3. 更新完了を待機:
   ```bash
   aws cloudformation wait stack-update-complete --stack-name django-ecs-service-staging-simple
   ```

**デプロイ前の必須確認事項**:
- [ ] 現在のスタック名を確認する
- [ ] デプロイスクリプトが正しいスタック名を使用しているか確認
- [ ] 新しいDockerイメージがECRにプッシュされているか確認 