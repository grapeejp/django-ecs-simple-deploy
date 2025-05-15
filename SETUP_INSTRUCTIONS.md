# Django ECS Simple Deploy - セットアップ手順

このドキュメントでは、Django ECS Simple Deployプロジェクトの環境構築とデプロイ手順を詳しく説明します。

## 前提条件

* AWSアカウント
* AWS CLIのインストールと設定
* Docker
* Python 3.11以上
* Git

## 1. 初期セットアップ

### リポジトリのクローン

```bash
git clone https://github.com/yourusername/django-ecs-simple-deploy.git
cd django-ecs-simple-deploy
```

### 仮想環境のセットアップ

```bash
# 仮想環境の作成
python -m venv .venv

# 仮想環境の有効化
# Linux/Mac
source .venv/bin/activate
# Windows
.venv\Scripts\activate

# 依存パッケージのインストール
pip install -r app/requirements.txt
```

### AWS認証情報の設定

ステージング環境と本番環境それぞれに対応する環境変数ファイルを作成します。

#### `.env.staging`ファイルの作成

```
AWS_ACCOUNT_ID=your_aws_account_id
AWS_REGION=ap-northeast-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

#### `.env.production`ファイルの作成

```
AWS_ACCOUNT_ID=your_aws_account_id
AWS_REGION=ap-northeast-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

**注意**: `.env.*`ファイルに含まれる認証情報はGitに公開しないよう注意してください。`.gitignore`に記載されていることを確認してください。

### IAMユーザーの権限設定

デプロイ用のIAMユーザーに必要な権限：

* AmazonECR-FullAccess
* AmazonECS-FullAccess
* CloudWatchFullAccess
* AmazonS3FullAccess
* AmazonSecretsManagerReadWrite
* AmazonRDSFullAccess
* CloudFormationFullAccess
* IAMFullAccess
* ElasticLoadBalancingFullAccess
* EC2FullAccess

**注意**: 本番環境では、最小権限の原則に従い、より限定的な権限設定をすることをお勧めします。

## 2. ローカル開発環境の構築

### Djangoアプリケーションの実行

```bash
cd app
python manage.py migrate
python manage.py runserver
```

ブラウザで http://localhost:8000 にアクセスして動作確認ができます。

### Dockerによるローカル実行

```bash
# Dockerイメージのビルド
docker build -t django-ecs-app -f docker/Dockerfile .

# コンテナの実行
docker run -p 8000:8000 django-ecs-app
```

## 3. AWS環境へのデプロイ

### ステージング環境へのデプロイ

```bash
./deploy.sh staging
```

### 本番環境へのデプロイ

```bash
./deploy.sh production
```

## 4. デプロイスクリプトの仕組み

`deploy.sh`スクリプトは以下の処理を実行します：

1. **環境変数の読み込み**
   - ステージングまたは本番用の`.env.*`ファイルから設定を読み込み

2. **ECRへのログイン**
   - AWS ECRにDockerクライアントからログイン

3. **ECRリポジトリの確認/作成**
   - リポジトリが存在しない場合は新規作成

4. **Dockerイメージのビルドとプッシュ**
   - ARM64→x86_64のクロスプラットフォームビルド
   - ECRへのイメージプッシュ

5. **AWS Secrets Managerの設定**
   - シークレットの確認/作成（例: Django SECRET_KEY）

6. **CloudFormationスタックのデプロイ**
   - ECSクラスタースタックの確認/作成
   - ECSサービススタックの作成

7. **デプロイ情報の表示**
   - アプリケーションのアクセスURL表示

## 5. CloudFormationスタックの詳細

### ecs-cluster.yml

基本インフラストラクチャを定義するスタック：

* VPC、サブネット、インターネットゲートウェイ
* セキュリティグループ
* Application Load Balancer (ALB)
* ECSクラスター
* IAMロール

### ecs-service.yml / ecs-service-staging.yml

アプリケーションサービスを定義するスタック：

* ECSタスク定義
* ECSサービス
* ALBリスナールール
* CloudWatchアラーム
* Auto Scaling設定

## 6. デプロイ後の確認と監視

1. CloudFormationコンソールでスタックのステータス確認
2. ECSコンソールでタスクの状態確認
3. CloudWatch Logsでアプリケーションログの確認
4. ALBのターゲットグループでヘルスチェック状態確認

## 7. アーキテクチャ対応の重要ポイント

Apple Silicon Mac（M1/M2/M3 - ARM64アーキテクチャ）からデプロイする場合の注意点：

* Dockerイメージビルド時に`--platform=linux/amd64`オプションを必ず指定（deploy.shに組み込み済み）
* `exec format error`が発生した場合はプラットフォーム指定を確認

## 8. よくあるトラブルとその対処法

### CloudFormationスタックのデプロイ失敗

* スタックイベントでエラー原因を確認
```bash
aws cloudformation describe-stack-events --stack-name <スタック名> --region <リージョン>
```

* ROLLBACK_COMPLETE状態のスタックは再デプロイ前に削除が必要
```bash
aws cloudformation delete-stack --stack-name <スタック名> --region <リージョン>
```

### ECSタスクが起動しない

* CloudWatch Logsでコンテナログを確認
* タスク定義のリソース設定（CPU/メモリ）を確認
* セキュリティグループの設定を確認

### アラーム名の競合エラー

* CloudFormationテンプレートのアラーム名に一意の識別子（TimestampSuffix）が追加されていることを確認

## 9. セキュリティ強化のポイント

* IAMロールの最小権限設定
* セキュリティグループの最小限のポート公開
* ALBでのHTTPS設定
* S3とCloudFrontによる静的ファイル配信
* AWS WAFによるウェブアプリケーション保護
* RDSのプライベートサブネット配置

## 10. CI/CD構築のポイント

GitHubActionsでCI/CDを構築する場合の設定例：

```yaml
name: Deploy to ECS

on:
  push:
    branches: [ main, develop ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ secrets.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build and push image to ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: django-ecs-app
        ENVIRONMENT: ${{ github.ref == 'refs/heads/main' && 'production' || 'staging' }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:latest --platform=linux/amd64 -f docker/Dockerfile .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
    
    - name: Deploy to ECS
      env:
        ENVIRONMENT: ${{ github.ref == 'refs/heads/main' && 'production' || 'staging' }}
      run: |
        ./deploy.sh $ENVIRONMENT
```

必要なGitHub Secrets:
* AWS_ACCESS_KEY_ID
* AWS_SECRET_ACCESS_KEY
* AWS_REGION
* AWS_ACCOUNT_ID 