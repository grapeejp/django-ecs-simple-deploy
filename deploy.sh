#!/bin/bash
set -e

# 色の設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# タイトル表示
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}      Django ECS Simple Deploy - デプロイスクリプト${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 環境変数の読み込み
echo -e "${GREEN}[1/7] 環境変数を読み込み中...${NC}"
if [ ! -f .env ]; then
  echo -e "${RED}エラー: .envファイルが見つかりません${NC}"
  exit 1
fi

# 必要な環境変数の確認
export AWS_ACCOUNT_ID=$(grep AWS_ACCOUNT_ID .env | cut -d '=' -f2)
export AWS_REGION=$(grep AWS_REGION .env | cut -d '=' -f2)
export AWS_ACCESS_KEY_ID=$(grep AWS_ACCESS_KEY_ID .env | cut -d '=' -f2)
export AWS_SECRET_ACCESS_KEY=$(grep AWS_SECRET_ACCESS_KEY .env | cut -d '=' -f2)

# 環境変数のチェック
if [ -z "$AWS_ACCOUNT_ID" ] || [ -z "$AWS_REGION" ] || [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
  echo -e "${RED}エラー: .envファイルに必要なAWS設定がありません${NC}"
  echo "必要な設定: AWS_ACCOUNT_ID, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
  exit 1
fi

echo -e "AWS アカウント ID: ${YELLOW}$AWS_ACCOUNT_ID${NC}"
echo -e "リージョン: ${YELLOW}$AWS_REGION${NC}"
echo -e "${GREEN}環境変数の読み込みが完了しました✓${NC}"
echo ""

# ECRへのログイン
echo -e "${GREEN}[2/7] Amazon ECRにログイン中...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
echo -e "${GREEN}ECRへのログインが完了しました✓${NC}"
echo ""

# ECRリポジトリの作成（存在しない場合）
echo -e "${GREEN}[3/7] ECRリポジトリを確認/作成中...${NC}"
if ! aws ecr describe-repositories --repository-names django-ecs-app --region $AWS_REGION &> /dev/null; then
  echo "リポジトリが存在しないため作成します..."
  aws ecr create-repository --repository-name django-ecs-app --region $AWS_REGION
  echo -e "${GREEN}リポジトリの作成が完了しました✓${NC}"
else
  echo -e "${GREEN}リポジトリは既に存在します✓${NC}"
fi
echo ""

# Dockerイメージのビルドとプッシュ
echo -e "${GREEN}[4/7] Dockerイメージをビルド中...${NC}"
IMAGE_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:latest
docker build -t $IMAGE_URI -f docker/Dockerfile .
echo -e "${GREEN}ビルドが完了しました✓${NC}"
echo ""

echo -e "${GREEN}イメージをECRにプッシュ中...${NC}"
docker push $IMAGE_URI
echo -e "${GREEN}プッシュが完了しました✓${NC}"
echo ""

# AWS Secrets Managerでシークレット作成
echo -e "${GREEN}[5/7] AWS Secrets Managerでシークレットを確認/作成中...${NC}"
if ! aws secretsmanager describe-secret --secret-id django-ecs-secrets --region $AWS_REGION &> /dev/null; then
  echo "シークレットが存在しないため作成します..."
  aws secretsmanager create-secret \
      --name django-ecs-secrets \
      --description "Django ECS アプリケーションのシークレット" \
      --secret-string "{\"SECRET_KEY\":\"$(openssl rand -base64 32)\"}" \
      --region $AWS_REGION
  echo -e "${GREEN}シークレットの作成が完了しました✓${NC}"
else
  echo -e "${GREEN}シークレットは既に存在します✓${NC}"
fi
echo ""

# CloudFormationスタックのデプロイ
echo -e "${GREEN}[6/7] CloudFormationスタックをデプロイ中...${NC}"

# タイムスタンプの生成
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# ステージング環境のECSクラスタースタックの確認
if ! aws cloudformation describe-stacks --stack-name django-ecs-cluster-staging --region $AWS_REGION &> /dev/null; then
  echo "ステージング用ECSクラスタースタックをデプロイ中..."
  aws cloudformation create-stack \
    --stack-name django-ecs-cluster-staging \
    --template-body file://cloudformation/ecs-cluster.yml \
    --capabilities CAPABILITY_IAM \
    --region $AWS_REGION
  
  echo "スタックの作成を待機中... (約5分かかります)"
  aws cloudformation wait stack-create-complete --stack-name django-ecs-cluster-staging --region $AWS_REGION
  echo -e "${GREEN}ステージング用ECSクラスタースタックのデプロイが完了しました✓${NC}"
else
  echo -e "${GREEN}ステージング用ECSクラスタースタックは既に存在します✓${NC}"
fi

# ステージング環境のECSサービススタックの作成
echo "ステージング用ECSサービススタックをデプロイ中..."
aws cloudformation create-stack \
  --stack-name django-ecs-service-staging-${TIMESTAMP} \
  --template-body file://cloudformation/ecs-service-staging.yml \
  --parameters \
    ParameterKey=ImageUrl,ParameterValue=$IMAGE_URI \
    ParameterKey=TimestampSuffix,ParameterValue=${TIMESTAMP} \
  --region $AWS_REGION

echo "スタックの作成を待機中... (約3分かかります)"
aws cloudformation wait stack-create-complete --stack-name django-ecs-service-staging-${TIMESTAMP} --region $AWS_REGION
echo -e "${GREEN}ステージング用ECSサービススタックのデプロイが完了しました✓${NC}"

# ALB DNS名の取得とアクセス方法の表示
echo -e "${GREEN}[7/7] デプロイ情報を取得中...${NC}"
ALB_DNS=$(aws cloudformation describe-stacks \
  --stack-name django-ecs-cluster \
  --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNSName'].OutputValue" \
  --output text \
  --region $AWS_REGION)

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}デプロイが完了しました！${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "アプリケーションには以下のURLからアクセスできます:"
echo -e "${YELLOW}http://$ALB_DNS${NC}"
echo ""
echo -e "注意: DNSの伝播には数分かかる場合があります。"
echo -e "しばらく待ってからアクセスしてください。"
echo ""
echo -e "${BLUE}================================================${NC}" 