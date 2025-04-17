# Terraformによるインフラ構築ガイド

本ドキュメントでは、Terraformを使用してAWS上にDjangoアプリケーション実行環境を構築する手順を説明します。

## 前提条件

- Terraformのインストール（バージョン1.0.0以上）
- AWS CLIのインストールと設定
- AWSアカウントとアクセス権限

## ディレクトリ構造

Terraformコードは以下のディレクトリ構造で管理します：

```
terraform/
├── environments/
│   ├── prod/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── staging/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── modules/
│   ├── networking/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── ecs/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── rds/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── alb/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── scripts/
    └── apply.sh
```

## セットアップ手順

### 1. Terraformのインストール

macOSの場合：

```bash
brew install terraform
```

他のOSの場合は[Terraformの公式サイト](https://www.terraform.io/downloads.html)を参照してください。

### 2. Terraformの初期化

```bash
cd terraform/environments/staging
terraform init
```

### 3. 実行計画の確認

```bash
terraform plan
```

### 4. インフラの構築

```bash
terraform apply
```

確認メッセージが表示されたら `yes` と入力して実行します。

## モジュール構成

### ネットワークモジュール

`modules/networking/main.tf`:

```hcl
# VPCの作成
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc-${var.environment}"
  }
}

# パブリックサブネットの作成
resource "aws_subnet" "public" {
  count             = length(var.public_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.public_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.project_name}-public-subnet-${count.index}-${var.environment}"
  }
}

# プライベートサブネットの作成
resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.project_name}-private-subnet-${count.index}-${var.environment}"
  }
}

# インターネットゲートウェイの作成
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw-${var.environment}"
  }
}

# EIPの作成（NATゲートウェイ用）
resource "aws_eip" "nat" {
  count = length(var.public_subnet_cidrs)
  vpc   = true

  tags = {
    Name = "${var.project_name}-eip-${count.index}-${var.environment}"
  }
}

# NATゲートウェイの作成
resource "aws_nat_gateway" "main" {
  count         = length(var.public_subnet_cidrs)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "${var.project_name}-nat-${count.index}-${var.environment}"
  }
}

# パブリックルートテーブルの作成
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt-${var.environment}"
  }
}

# プライベートルートテーブルの作成
resource "aws_route_table" "private" {
  count  = length(var.private_subnet_cidrs)
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name = "${var.project_name}-private-rt-${count.index}-${var.environment}"
  }
}

# パブリックサブネットとルートテーブルの関連付け
resource "aws_route_table_association" "public" {
  count          = length(var.public_subnet_cidrs)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# プライベートサブネットとルートテーブルの関連付け
resource "aws_route_table_association" "private" {
  count          = length(var.private_subnet_cidrs)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}
```

### ECSモジュール

`modules/ecs/main.tf`:

```hcl
# ECSクラスターの作成
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# CloudWatch Logsグループの作成
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.project_name}-${var.environment}"
  retention_in_days = var.log_retention_days
}

# タスク実行ロールの作成
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.project_name}-task-execution-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# タスク実行ロールへのポリシーアタッチ
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# タスクロールの作成
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.project_name}-task-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# タスク定義の作成
resource "aws_ecs_task_definition" "main" {
  family                   = "${var.project_name}-task-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "${var.project_name}-container-${var.environment}"
      image     = var.container_image
      essential = true
      
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      
      environment = var.container_environment
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# セキュリティグループの作成
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-ecs-tasks-sg-${var.environment}"
  description = "Allow inbound access from the ALB only"
  vpc_id      = var.vpc_id

  ingress {
    protocol        = "tcp"
    from_port       = var.container_port
    to_port         = var.container_port
    security_groups = [var.alb_security_group_id]
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ECSサービスの作成
resource "aws_ecs_service" "main" {
  name                               = "${var.project_name}-service-${var.environment}"
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = aws_ecs_task_definition.main.arn
  desired_count                      = var.service_desired_count
  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200
  launch_type                        = "FARGATE"
  scheduling_strategy                = "REPLICA"
  health_check_grace_period_seconds  = 60

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = var.private_subnet_ids
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "${var.project_name}-container-${var.environment}"
    container_port   = var.container_port
  }

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }
}

# Auto Scaling設定
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = var.auto_scaling_max_capacity
  min_capacity       = var.auto_scaling_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.main.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# CPU使用率に基づくスケーリングポリシー
resource "aws_appautoscaling_policy" "ecs_policy_cpu" {
  name               = "${var.project_name}-cpu-auto-scaling-${var.environment}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}
```

### ALBモジュール

`modules/alb/main.tf`:

```hcl
# ALBセキュリティグループの作成
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg-${var.environment}"
  description = "Allow HTTP/HTTPS inbound traffic"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ALBの作成
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "production" ? true : false

  tags = {
    Environment = var.environment
    Name        = "${var.project_name}-alb-${var.environment}"
  }
}

# ターゲットグループの作成
resource "aws_lb_target_group" "main" {
  name        = "${var.project_name}-tg-${var.environment}"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = var.health_check_path
    port                = "traffic-port"
    matcher             = "200"
  }
}

# HTTPリスナーの作成
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPSリスナーの作成
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}
```

### RDSモジュール

`modules/rds/main.tf`:

```hcl
# RDSパラメータグループの作成
resource "aws_db_parameter_group" "main" {
  name   = "${var.project_name}-pg-${var.environment}"
  family = "postgres13"

  parameter {
    name  = "log_connections"
    value = "1"
  }
}

# RDSサブネットグループの作成
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-subnet-group-${var.environment}"
  subnet_ids = var.database_subnet_ids

  tags = {
    Name = "${var.project_name}-subnet-group-${var.environment}"
  }
}

# RDSセキュリティグループの作成
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg-${var.environment}"
  description = "Allow inbound traffic from ECS tasks only"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from ECS tasks"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# RDSインスタンスの作成
resource "aws_db_instance" "main" {
  identifier             = "${var.project_name}-db-${var.environment}"
  engine                 = "postgres"
  engine_version         = "13.7"
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  storage_type           = "gp2"
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.main.name
  publicly_accessible    = false
  skip_final_snapshot    = var.environment != "production"
  deletion_protection    = var.environment == "production"
  backup_retention_period = var.environment == "production" ? 7 : 1
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"
  multi_az               = var.environment == "production"

  tags = {
    Name        = "${var.project_name}-db-${var.environment}"
    Environment = var.environment
  }
}
```

## ステージング環境の構成例

`environments/staging/main.tf`:

```hcl
provider "aws" {
  region = var.region
}

terraform {
  backend "s3" {
    bucket  = "terraform-state-django-ecs"
    key     = "staging/terraform.tfstate"
    region  = "ap-northeast-1"
    encrypt = true
  }
}

module "networking" {
  source = "../../modules/networking"

  project_name         = var.project_name
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  availability_zones   = var.availability_zones
  region               = var.region
}

module "alb" {
  source = "../../modules/alb"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.networking.vpc_id
  public_subnet_ids = module.networking.public_subnet_ids
  container_port    = var.container_port
  health_check_path = var.health_check_path
  certificate_arn   = var.certificate_arn
}

module "rds" {
  source = "../../modules/rds"

  project_name         = var.project_name
  environment          = var.environment
  vpc_id               = module.networking.vpc_id
  database_subnet_ids  = module.networking.private_subnet_ids
  ecs_security_group_id = module.ecs.ecs_security_group_id
  db_instance_class    = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
  db_name              = var.db_name
  db_username          = var.db_username
  db_password          = var.db_password
}

module "ecs" {
  source = "../../modules/ecs"

  project_name           = var.project_name
  environment            = var.environment
  region                 = var.region
  vpc_id                 = module.networking.vpc_id
  private_subnet_ids     = module.networking.private_subnet_ids
  alb_security_group_id  = module.alb.alb_security_group_id
  target_group_arn       = module.alb.target_group_arn
  container_image        = var.container_image
  container_port         = var.container_port
  task_cpu               = var.task_cpu
  task_memory            = var.task_memory
  service_desired_count  = var.service_desired_count
  log_retention_days     = var.log_retention_days
  auto_scaling_min_capacity = var.auto_scaling_min_capacity
  auto_scaling_max_capacity = var.auto_scaling_max_capacity
  
  container_environment = [
    {
      name  = "DJANGO_SETTINGS_MODULE"
      value = "hello_django.settings.staging"
    },
    {
      name  = "DATABASE_URL"
      value = "postgres://${var.db_username}:${var.db_password}@${module.rds.db_endpoint}/${var.db_name}"
    },
    {
      name  = "ALLOWED_HOSTS"
      value = "${module.alb.alb_dns_name},staging.example.com"
    }
  ]
}
```

## 各環境の変数設定例

`environments/staging/variables.tf`:

```hcl
variable "region" {
  description = "AWS region"
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "Project name"
  default     = "django-ecs"
}

variable "environment" {
  description = "Environment name"
  default     = "staging"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.3.0/24", "10.0.4.0/24"]
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["ap-northeast-1a", "ap-northeast-1c"]
}

variable "container_image" {
  description = "Container image"
  default     = "xxxxxxxxxxxx.dkr.ecr.ap-northeast-1.amazonaws.com/django-ecs-app:latest"
}

variable "container_port" {
  description = "Container port"
  default     = 8000
}

variable "task_cpu" {
  description = "Task CPU units"
  default     = "256"
}

variable "task_memory" {
  description = "Task memory"
  default     = "512"
}

variable "service_desired_count" {
  description = "Number of tasks to run"
  default     = 2
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  default     = 30
}

variable "auto_scaling_min_capacity" {
  description = "Minimum number of tasks"
  default     = 2
}

variable "auto_scaling_max_capacity" {
  description = "Maximum number of tasks"
  default     = 4
}

variable "health_check_path" {
  description = "Health check path"
  default     = "/health/"
}

variable "certificate_arn" {
  description = "SSL certificate ARN"
  default     = ""
}

variable "db_instance_class" {
  description = "RDS instance class"
  default     = "db.t3.small"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage"
  default     = 20
}

variable "db_name" {
  description = "Database name"
  default     = "django"
}

variable "db_username" {
  description = "Database username"
  default     = "django"
}

variable "db_password" {
  description = "Database password"
  sensitive   = true
}
```

## 実用的な自動化スクリプト

`scripts/apply.sh`:

```bash
#!/bin/bash

# 環境変数の検証
if [ -z "$ENV" ]; then
  echo "ERROR: ENV環境変数が設定されていません"
  echo "使用例: ENV=staging ./scripts/apply.sh"
  exit 1
fi

# DBパスワードの検証
if [ -z "$TF_VAR_db_password" ]; then
  echo "ERROR: TF_VAR_db_password環境変数が設定されていません"
  echo "使用例: TF_VAR_db_password=mypassword ENV=staging ./scripts/apply.sh"
  exit 1
fi

# 環境ディレクトリへの移動
cd "$(dirname "$0")/../environments/$ENV" || {
  echo "ERROR: 環境ディレクトリが見つかりません: $ENV"
  exit 1
}

# Terraformの実行
echo "環境 $ENV に対してTerraformを実行します..."
terraform init
terraform validate
terraform plan
echo "インフラ変更を適用しますか？ (yes/no)"
read -r apply_changes

if [ "$apply_changes" = "yes" ]; then
  terraform apply
  echo "完了しました！"
else
  echo "キャンセルされました"
fi
```

## Terraformを使用した迅速なデプロイ手順

### 初回デプロイ

```bash
# 必要な環境変数を設定
export TF_VAR_db_password="secure_password_here"
export ENV=staging

# デプロイスクリプトを実行
./scripts/apply.sh
```

### 継続的デプロイ（CI/CD）との連携

GitHub Actionsで継続的デプロイを自動化する例：

```yaml
name: Deploy Infrastructure

on:
  push:
    branches:
      - main
    paths:
      - 'terraform/**'

jobs:
  terraform:
    name: 'Terraform'
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.0.0
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1
      
      - name: Terraform Init
        working-directory: terraform/environments/staging
        run: terraform init
      
      - name: Terraform Plan
        working-directory: terraform/environments/staging
        run: terraform plan -out=tfplan
        env:
          TF_VAR_db_password: ${{ secrets.DB_PASSWORD }}
      
      - name: Terraform Apply
        working-directory: terraform/environments/staging
        run: terraform apply -auto-approve tfplan
```

## よくある問題と解決策

### 1. ステート管理

リモートステートを使用してチーム間で状態を共有します：

```hcl
terraform {
  backend "s3" {
    bucket  = "terraform-state-django-ecs"
    key     = "staging/terraform.tfstate"
    region  = "ap-northeast-1"
    encrypt = true
    dynamodb_table = "terraform-lock" # ステートロック用
  }
}
```

### 2. 機密情報の管理

以下の方法で機密情報を管理します：

- 環境変数として渡す: `export TF_VAR_db_password="secure_password"`
- AWS Secrets Managerと連携: `data "aws_secretsmanager_secret_version" "db_password" {}`
- Terraformのvariableを使用し、適用時に入力: `variable "db_password" { sensitive = true }`

### 3. ステート破損時の復旧

1. バックアップから復元
   ```bash
   aws s3 cp s3://terraform-state-django-ecs/staging/terraform.tfstate.backup ./terraform.tfstate
   ```

2. インポートによる再構築
   ```bash
   terraform import aws_vpc.main vpc-12345678
   ```

## 次のステップ

- ステートファイルのバージョン管理とロック機構の追加
- 複数リージョンへのデプロイ対応
- AWS Organizationsとの統合
- コスト最適化設定の追加 