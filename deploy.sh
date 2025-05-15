#!/bin/bash
set -e

# 色の設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 引数のチェック
if [ $# -ne 1 ]; then
  echo -e "${RED}エラー: 引数が無効です${NC}"
  echo "使用方法: ./deploy.sh [staging|production]"
  exit 1
fi

ENVIRONMENT=$1

if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
  echo -e "${RED}エラー: 環境は 'staging' または 'production' を指定してください${NC}"
  echo "使用方法: ./deploy.sh [staging|production]"
  exit 1
fi

# 環境設定ファイルの選択
ENV_FILE=".env"
if [ "$ENVIRONMENT" == "staging" ] && [ -f ".env.staging" ]; then
  ENV_FILE=".env.staging"
elif [ "$ENVIRONMENT" == "production" ] && [ -f ".env.production" ]; then
  ENV_FILE=".env.production"
fi

# タイトル表示
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Django ECS Simple Deploy - デプロイスクリプト${NC}"
echo -e "${BLUE}     環境: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 環境変数の読み込み
echo -e "${GREEN}[1/7] 環境変数を読み込み中 (${ENV_FILE})...${NC}"
if [ ! -f ${ENV_FILE} ]; then
  echo -e "${RED}エラー: ${ENV_FILE}ファイルが見つかりません${NC}"
  exit 1
fi

# 必要な環境変数の確認
export AWS_ACCOUNT_ID=$(grep AWS_ACCOUNT_ID ${ENV_FILE} | cut -d '=' -f2)
export AWS_REGION=$(grep AWS_REGION ${ENV_FILE} | cut -d '=' -f2)
export AWS_ACCESS_KEY_ID=$(grep AWS_ACCESS_KEY_ID ${ENV_FILE} | cut -d '=' -f2)
export AWS_SECRET_ACCESS_KEY=$(grep AWS_SECRET_ACCESS_KEY ${ENV_FILE} | cut -d '=' -f2)

# 環境変数のチェック
if [ -z "$AWS_ACCOUNT_ID" ] || [ -z "$AWS_REGION" ] || [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
  echo -e "${RED}エラー: ${ENV_FILE}ファイルに必要なAWS設定がありません${NC}"
  echo "必要な設定: AWS_ACCOUNT_ID, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
  exit 1
fi

echo -e "AWS アカウント ID: ${YELLOW}$AWS_ACCOUNT_ID${NC}"
echo -e "リージョン: ${YELLOW}$AWS_REGION${NC}"
echo -e "環境: ${YELLOW}$ENVIRONMENT${NC}"
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
docker build -t $IMAGE_URI --platform=linux/amd64 -f docker/Dockerfile .
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

# ECSクラスタースタックの確認
if ! aws cloudformation describe-stacks --stack-name django-ecs-cluster-${ENVIRONMENT} --region $AWS_REGION &> /dev/null; then
  echo "${ENVIRONMENT}用ECSクラスタースタックをデプロイ中..."
  aws cloudformation create-stack \
    --stack-name django-ecs-cluster-${ENVIRONMENT} \
    --template-body file://cloudformation/ecs-cluster.yml \
    --parameters \
      ParameterKey=Environment,ParameterValue=${ENVIRONMENT} \
    --capabilities CAPABILITY_IAM \
    --region $AWS_REGION
  
  echo "スタックの作成を待機中... (約5分かかります)"
  aws cloudformation wait stack-create-complete --stack-name django-ecs-cluster-${ENVIRONMENT} --region $AWS_REGION
  echo -e "${GREEN}${ENVIRONMENT}用ECSクラスタースタックのデプロイが完了しました✓${NC}"
else
  echo -e "${GREEN}${ENVIRONMENT}用ECSクラスタースタックは既に存在します✓${NC}"
fi

# ECSサービススタックの作成
echo "${ENVIRONMENT}用ECSサービススタックをデプロイ中..."

# 環境に応じたテンプレートを選択
if [ "$ENVIRONMENT" == "staging" ]; then
  TEMPLATE_FILE="cloudformation/ecs-service-staging.yml"
  # ステージング環境用のパラメータセット
  PARAMETERS="ParameterKey=ImageUrl,ParameterValue=$IMAGE_URI ParameterKey=TimestampSuffix,ParameterValue=-${TIMESTAMP}"
else
  TEMPLATE_FILE="cloudformation/ecs-service.yml"
  # 本番環境用のパラメータセット
  PARAMETERS="ParameterKey=ImageUrl,ParameterValue=$IMAGE_URI ParameterKey=Environment,ParameterValue=${ENVIRONMENT} ParameterKey=TimestampSuffix,ParameterValue=${TIMESTAMP}"
fi

aws cloudformation create-stack \
  --stack-name django-ecs-service-${ENVIRONMENT}-${TIMESTAMP} \
  --template-body file://${TEMPLATE_FILE} \
  --parameters ${PARAMETERS} \
  --capabilities CAPABILITY_IAM \
  --region $AWS_REGION

echo "スタックの作成を待機中... (約3分かかります)"
aws cloudformation wait stack-create-complete --stack-name django-ecs-service-${ENVIRONMENT}-${TIMESTAMP} --region $AWS_REGION
echo -e "${GREEN}${ENVIRONMENT}用ECSサービススタックのデプロイが完了しました✓${NC}"

# ALB DNS名の取得とアクセス方法の表示
echo -e "${GREEN}[7/7] デプロイ情報を取得中...${NC}"
ALB_DNS=$(aws cloudformation describe-stacks \
  --stack-name django-ecs-cluster-${ENVIRONMENT} \
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
echo -e "環境: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "注意: DNSの伝播には数分かかる場合があります。"
echo -e "しばらく待ってからアクセスしてください。"
echo ""
echo -e "${BLUE}================================================${NC}" 