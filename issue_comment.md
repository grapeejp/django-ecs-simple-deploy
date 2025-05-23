## 「グレイプらしさチェッカー」開発の作業フロー

### 1. 環境準備
- 新しいfeatureブランチの作成
  ```
  git checkout -b feature/grapecheck
  ```
- AWS Bedrockに必要なライブラリのインストール
  ```
  pip install boto3
  ```

### 2. アプリケーション構造作成
- Djangoアプリの作成
  ```
  cd app
  python manage.py startapp grapecheck
  ```
- アプリ設定の追加（settings.pyにアプリを登録）

### 3. モデル設計・実装
- カテゴリデータのモデル作成
- 評価結果保存用モデル作成
- マイグレーション実行

### 4. AWS連携基盤構築
- AWS認証情報の設定
- BedrockクライアントのServiceクラス実装
- プロンプトテンプレート作成

### 5. ビジネスロジック実装
- 文体分析機能
- カテゴリ別評価ロジック
- スコアリングシステム
- 改善提案生成

### 6. UI実装
- テンプレート作成
  - メイン入力フォーム
  - カテゴリ選択UI
  - 結果表示画面
- ビューの実装
- URL設定

### 7. 非同期処理設定
- Celeryタスク設定
- 処理状況表示機能

### 8. テスト作成・実行
- 単体テスト
- 統合テスト
- カテゴリ別評価精度の検証

### 9. デプロイ準備
- AWS IAM設定確認
- ECS/Fargate設定調整
- 環境変数設定

### 10. レビュー・マージ
- コードレビュー依頼
- Pull Request作成
- developブランチへのマージ 