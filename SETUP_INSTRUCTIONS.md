# Django ECS リポジトリセットアップ手順

## GitHubリポジトリ作成

1. GitHubの[grapeejp](https://github.com/grapeejp)組織アカウントにアクセス
2. 「New repository」ボタンをクリック
3. 以下の設定でリポジトリを作成
   - Repository name: `django-ecs-simple-deploy`
   - Description: AWS ECSでDjangoアプリケーションを簡単にデプロイするためのテンプレート
   - Visibility: Public
   - Initialize with README: チェックしない
   - Add .gitignore: None
   - License: MIT

## ローカルリポジトリと連携

```bash
# ローカルで作成したリポジトリをGitHubにプッシュ
cd ~/Desktop/django-ecs-simple-deploy
git remote add origin https://github.com/grapeejp/django-ecs-simple-deploy.git
git branch -M main
git push -u origin main
```

## 追加で必要な設定

### GitHub Secrets設定

GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」から以下のシークレットを追加

- `AWS_ACCESS_KEY_ID`: AWS IAMユーザーのアクセスキーID
- `AWS_SECRET_ACCESS_KEY`: AWS IAMユーザーのシークレットアクセスキー
- `AWS_REGION`: AWSリージョン（例：ap-northeast-1）
- `AWS_ACCOUNT_ID`: AWSアカウントID

### アプリケーション実装

1. ヘルスチェックエンドポイントの追加 (完了済み)
2. Djangoプロジェクトの初期設定
   - Djangoプロジェクトに以下を追加:
     - `app/config/urls.py`にヘルスチェックエンドポイントのルーティング
     - S3静的ファイル設定
     - CloudWatch Logs設定
     - PostgreSQL接続設定

## 今後の開発作業

### 優先度の高いタスク

1. **Djangoプロジェクトの実装**
   - `app/config/settings.py`のカスタマイズ（環境変数対応）
   - RDS PostgreSQL連携
   - S3静的ファイル連携
   - X-Rayトレース機能追加

2. **RDS設定の追加**
   - CloudFormationテンプレートにRDS設定を追加
   - DBマイグレーション用のデプロイスクリプト拡張

3. **ドキュメント強化**
   - アーキテクチャ図の改善
   - トラブルシューティングセクション追加
   - AWS費用最適化ガイド

### 中期的なタスク

1. **監視体制の強化**
   - CloudWatchダッシュボード自動作成
   - アラート設定の詳細化

2. **セキュリティ強化**
   - WAF設定の追加
   - セキュアヘッダーの実装

3. **CI/CD改善**
   - テスト自動化
   - ブルー/グリーンデプロイ対応

## 参考情報

- [AWS Fargate公式ドキュメント](https://docs.aws.amazon.com/ja_jp/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [Django on AWS ECSのベストプラクティス](https://testdriven.io/blog/deploying-django-to-ecs-with-terraform/)
- [CloudFormation Template Reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-reference.html) 