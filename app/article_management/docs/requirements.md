# 記事管理システム要件定義

## 概要
現在のスプレッドシート管理を、既存のDjangoシステムに統合したWebアプリに置き換え、記事管理業務を効率化します。

## Phase 1: 基本機能（MVP）

### 1. データモデル

#### Article（記事）
- `article_id`: 記事番号（自動採番）
- `applicant`: 申請者（User FK）
- `writer`: ライター（User FK, nullable）
- `status`: ステータス（申請中/承認NG/送信済/不明）
- `title`: 記事タイトル
- `content`: 記事内容・概要
- `reference_url`: 参考URL
- `social_media_users`: 使用するSNSユーザー（M2M）
- `created_at`: 申請日時
- `updated_at`: 更新日時
- `published_at`: 公開日時（nullable）
- `facebook_text`: Facebook投稿テキスト
- `notes`: 備考

#### SocialMediaUser（SNSユーザー）
- `handle_name`: ハンドルネーム
- `platform`: プラットフォーム（Twitter/Instagram/TikTok/YouTube）
- `profile_url`: プロフィールURL
- `status`: ステータス（OK/NG）
- `permission_date`: 許諾取得日
- `permission_expires`: 許諾期限（nullable）
- `usage_conditions`: 利用条件
- `ng_reason`: NG理由（NGの場合）
- `notes`: 備考

### 2. 機能要件

#### 記事管理
- 記事の作成・編集・削除
- 記事番号の自動採番
- ステータス管理（ワークフロー）
- 記事検索（タイトル、内容、ステータス、日付範囲）
- 一覧表示（ソート、フィルタリング、ページネーション）

#### SNSユーザー許諾管理
- OKユーザー/NGユーザーの登録・管理
- 記事作成時の許諾チェック
- NGユーザー使用時のアラート表示
- 許諾期限の管理とアラート

#### ユーザー管理
- 既存のGoogle認証（@grapee.jp）を活用
- 権限レベル：
  - ライター：記事の作成・自分の記事の編集
  - 編集者：全記事の編集・承認
  - 管理者：システム全体の管理

### 3. UI要件

#### ダッシュボード
- 申請中の記事数
- 承認待ちの記事数
- 本日の締切記事
- 最近の活動履歴

#### 記事一覧画面
- テーブル形式での表示
- ステータスによる色分け
- クイック検索
- 一括操作

#### 記事作成・編集画面
- SNSユーザー選択時の許諾状況表示
- NGユーザー選択時の警告
- 自動保存機能

## Phase 2: 高度な機能

### AI機能統合
- 記事重複チェック（既存Bedrock活用）
- カテゴリ自動推奨
- タイトル改善提案

### 分析機能
- ライター別の記事数・承認率
- 月次レポート生成
- 記事カテゴリ別の統計

## Phase 3: 外部連携

### 通知機能
- ChatWork通知（承認依頼、期限アラート）
- メール通知（オプション）

### CMS連携
- WordPress自動投稿（将来実装）
- SNS投稿スケジュール管理

## 技術仕様

### 使用技術
- Django 5.2（既存システム）
- PostgreSQL（既存DB）
- AWS Bedrock（既存AI基盤）
- Google OAuth（既存認証）

### セキュリティ
- @grapee.jpドメイン制限
- 権限ベースのアクセス制御
- 操作ログの記録

## 開発スケジュール

- Phase 1: 2週間
- Phase 2: 1週間
- Phase 3: 1週間

合計: 約1ヶ月