# ECS デプロイ手順

このドキュメントでは Django アプリケーションを AWS ECS にデプロイする手順を説明します。

## 1. 環境変数の設定

`.env` ファイルをルートディレクトリに作成し、必要な環境変数を設定してください。
以下は `.env` ファイルの例です。

```
# Django環境変数
DEBUG=0
SECRET_KEY=your-secure-secret-key
DJANGO_ALLOWED_HOSTS=*
DATABASE_URL=sqlite:///db.sqlite3

# AWS設定
AWS_ACCOUNT_ID=<YOUR_AWS_ACCOUNT_ID>
AWS_REGION=ap-northeast-1
AWS_ACCESS_KEY_ID=<YOUR_ACCESS_KEY>
AWS_SECRET_ACCESS_KEY=<YOUR_SECRET_KEY>
AWS_STORAGE_BUCKET_NAME=<YOUR_S3_BUCKET_NAME>
AWS_S3_CUSTOM_DOMAIN=<YOUR_CLOUDFRONT_DOMAIN>

# ECS設定
ECR_REPOSITORY_NAME=django-ecs-app
ECS_CLUSTER_NAME=django-ecs-cluster
ECS_SERVICE_NAME=django-ecs-service
```

## 2. ローカル環境での動作確認

```bash
# 開発環境の起動
docker-compose up -d

# ブラウザでアクセス
# http://localhost:8001
```

## 3. ECR リポジトリへのプッシュ

```bash
# AWS CLI環境変数を設定
export AWS_ACCOUNT_ID=$(grep AWS_ACCOUNT_ID .env | cut -d '=' -f2)
export AWS_REGION=$(grep AWS_REGION .env | cut -d '=' -f2)

# ECRにログイン
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# リポジトリ作成（初回のみ）
aws ecr create-repository --repository-name django-ecs-app

# イメージビルドとプッシュ
docker build -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:latest -f docker/Dockerfile .
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:latest
```

## 4. AWS Secrets Manager でシークレット作成（初回のみ）

```bash
aws secretsmanager create-secret \
    --name django-ecs-secrets \
    --description "Django ECS アプリケーションのシークレット" \
    --secret-string "{\"SECRET_KEY\":\"your-secure-secret-key\"}"
```

## 5. CloudFormation スタック作成

```bash
# ECSクラスターのデプロイ
aws cloudformation create-stack \
  --stack-name django-ecs-cluster \
  --template-body file://cloudformation/ecs-cluster.yml \
  --capabilities CAPABILITY_IAM

# ECSサービスのデプロイ
aws cloudformation create-stack \
  --stack-name django-ecs-service \
  --template-body file://cloudformation/ecs-service.yml \
  --parameters ParameterKey=ImageUrl,ParameterValue=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:latest
```

## 6. ALB エンドポイントの確認

```bash
# ALBのDNS名を取得
aws cloudformation describe-stacks \
  --stack-name django-ecs-cluster \
  --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNSName'].OutputValue" \
  --output text
```

取得したDNS名にブラウザからアクセスし、Djangoのスタートアップ画面が表示されることを確認します。 