#!/bin/bash

# 本番環境デプロイスクリプト
# 使用方法: ./scripts/deploy-production.sh

set -e

# 環境変数の設定
export AWS_REGION="ap-northeast-1"
export AWS_ACCOUNT_ID="026090540679"
export ENVIRONMENT="production"

# カラー出力の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 本番環境デプロイ開始${NC}"
echo "=================================================="

# 確認プロンプト
echo -e "${YELLOW}⚠️  本番環境にデプロイしようとしています${NC}"
echo "本当に続行しますか？ (yes/no)"
read -r CONFIRM

if [[ $CONFIRM != "yes" ]]; then
    echo -e "${RED}❌ デプロイがキャンセルされました${NC}"
    exit 1
fi

# 現在のブランチ確認
CURRENT_BRANCH=$(git branch --show-current)
if [[ $CURRENT_BRANCH != "main" ]]; then
    echo -e "${YELLOW}⚠️  現在のブランチ: $CURRENT_BRANCH${NC}"
    echo "本番デプロイは通常mainブランチから行います。続行しますか？ (yes/no)"
    read -r BRANCH_CONFIRM
    if [[ $BRANCH_CONFIRM != "yes" ]]; then
        echo -e "${RED}❌ デプロイがキャンセルされました${NC}"
        exit 1
    fi
fi

# タイムスタンプ生成
TIMESTAMP=$(date +%Y%m%d%H%M%S)
IMAGE_TAG="production-${TIMESTAMP}"

echo -e "${BLUE}📦 Dockerイメージのビルド開始${NC}"

# Dockerイメージのビルド
docker build --platform=linux/amd64 -t django-ecs-app:$IMAGE_TAG -f docker/Dockerfile .

# ECRにログイン
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# ECRにイメージをプッシュ
IMAGE_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:$IMAGE_TAG"
docker tag django-ecs-app:$IMAGE_TAG $IMAGE_URL
docker push $IMAGE_URL

echo -e "${GREEN}✅ Dockerイメージのプッシュ完了: $IMAGE_URL${NC}"

# CloudFormationスタック名
CLUSTER_STACK_NAME="django-ecs-cluster-${ENVIRONMENT}"
SERVICE_STACK_NAME="django-ecs-service-${ENVIRONMENT}"

echo -e "${BLUE}☁️  CloudFormationデプロイ開始${NC}"

# クラスタースタックのデプロイ/更新
echo "クラスタースタックを確認中..."
if aws cloudformation describe-stacks --stack-name $CLUSTER_STACK_NAME &> /dev/null; then
    echo -e "${YELLOW}📝 既存のクラスタースタックを更新中...${NC}"
    aws cloudformation update-stack \
        --stack-name $CLUSTER_STACK_NAME \
        --template-body file://cloudformation/ecs-cluster-production.yml \
        --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
        --capabilities CAPABILITY_IAM
    
    # 更新完了を待機
    echo "クラスタースタック更新の完了を待機中..."
    aws cloudformation wait stack-update-complete --stack-name $CLUSTER_STACK_NAME
else
    echo -e "${GREEN}🆕 新しいクラスタースタックを作成中...${NC}"
    aws cloudformation create-stack \
        --stack-name $CLUSTER_STACK_NAME \
        --template-body file://cloudformation/ecs-cluster-production.yml \
        --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
        --capabilities CAPABILITY_IAM
    
    # 作成完了を待機
    echo "クラスタースタック作成の完了を待機中..."
    aws cloudformation wait stack-create-complete --stack-name $CLUSTER_STACK_NAME
fi

echo -e "${GREEN}✅ クラスタースタックのデプロイ完了${NC}"

# サービススタックのデプロイ/更新
echo "サービススタックを確認中..."
if aws cloudformation describe-stacks --stack-name $SERVICE_STACK_NAME &> /dev/null; then
    echo -e "${YELLOW}📝 既存のサービススタックを更新中...${NC}"
    aws cloudformation update-stack \
        --stack-name $SERVICE_STACK_NAME \
        --template-body file://cloudformation/ecs-service-production.yml \
        --parameters ParameterKey=ImageUrl,ParameterValue=$IMAGE_URL
    
    # 更新完了を待機
    echo "サービススタック更新の完了を待機中..."
    aws cloudformation wait stack-update-complete --stack-name $SERVICE_STACK_NAME
else
    echo -e "${GREEN}🆕 新しいサービススタックを作成中...${NC}"
    aws cloudformation create-stack \
        --stack-name $SERVICE_STACK_NAME \
        --template-body file://cloudformation/ecs-service-production.yml \
        --parameters ParameterKey=ImageUrl,ParameterValue=$IMAGE_URL
    
    # 作成完了を待機
    echo "サービススタック作成の完了を待機中..."
    aws cloudformation wait stack-create-complete --stack-name $SERVICE_STACK_NAME
fi

echo -e "${GREEN}✅ サービススタックのデプロイ完了${NC}"

# デプロイ結果の確認
echo -e "${BLUE}🔍 デプロイ結果確認${NC}"

# ECSサービスの状態確認
echo "ECSサービスの状態を確認中..."
aws ecs describe-services \
    --cluster $ENVIRONMENT-cluster \
    --services django-ecs-service-$ENVIRONMENT \
    --query 'services[0].{ServiceName:serviceName,Status:status,RunningCount:runningCount,DesiredCount:desiredCount}' \
    --output table

# ALBのDNS名取得
ALB_DNS=$(aws cloudformation describe-stacks \
    --stack-name $CLUSTER_STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`ApplicationLoadBalancer`].OutputValue' \
    --output text)

echo -e "${GREEN}🎉 本番環境デプロイ完了！${NC}"
echo "=================================================="
echo -e "${BLUE}📋 デプロイ情報${NC}"
echo "環境: $ENVIRONMENT"
echo "イメージ: $IMAGE_URL"
echo "ALB DNS: $ALB_DNS"
echo ""
echo -e "${BLUE}🔗 アクセスURL${NC}"
echo "本番環境: https://prod.grape-app.jp/"
echo "メインドメイン: https://grape-app.jp/"
echo "www: https://www.grape-app.jp/"
echo ""
echo -e "${YELLOW}⚠️  注意: DNS伝播には数分かかる場合があります${NC}"

# ヘルスチェック
echo -e "${BLUE}🏥 ヘルスチェック実行中...${NC}"
sleep 30
for i in {1..5}; do
    echo "ヘルスチェック試行 $i/5..."
    if curl -s -I https://prod.grape-app.jp/health/ | grep -q "200 OK"; then
        echo -e "${GREEN}✅ ヘルスチェック成功！${NC}"
        break
    else
        echo -e "${YELLOW}⏳ ヘルスチェック待機中...${NC}"
        sleep 30
    fi
done

echo -e "${GREEN}🎊 本番環境デプロイが正常に完了しました！${NC}" 