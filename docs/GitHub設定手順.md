# GitHub設定手順

このドキュメントでは、チーム開発に必要なGitHubリポジトリの設定手順を解説します。

## ブランチ保護ルールの設定

以下の手順でmainブランチとdevelopブランチを保護します。これにより、意図しない変更を防ぎ、コード品質を維持できます。

### 手順1: ブランチ保護設定画面へのアクセス

1. GitHubリポジトリのページを開く
2. 上部メニューの「Settings」タブをクリック
3. 左側メニューから「Branches」を選択
4. 「Branch protection rules」セクションの「Add rule」ボタンをクリック

### 手順2: mainブランチの保護ルール設定

以下の設定を行います：

1. 「Branch name pattern」に `main` と入力
2. 「Require a pull request before merging」にチェック
   - 「Require approvals」はチェックを外す（重要な変更のみレビュー対象のため）
3. 「Do not allow bypassing the above settings」にチェック
4. 「Save changes」ボタンをクリック

これにより、mainブランチへの直接プッシュが禁止され、プルリクエスト経由での変更のみが許可されます。

### 手順3: developブランチの保護ルール設定

「Add rule」ボタンをクリックして、developブランチ用の新しいルールを追加します。

1. 「Branch name pattern」に `develop` と入力
2. 「Require a pull request before merging」にチェック
   - 「Require approvals」はチェックを外す（重要な変更のみレビュー対象のため）
3. 「Do not allow bypassing the above settings」にチェック
4. 「Save changes」ボタンをクリック

### ブランチ保護設定の効果

これらの設定により以下の効果があります：

1. mainとdevelopブランチへの直接プッシュは禁止
2. すべての変更はプルリクエスト経由で行う必要がある
3. 「重要な変更」（PRテンプレートで判断）のみレビューが必要

## 自動Pull設定（開発者環境）

各開発者は以下の設定を行うことで、ブランチ切り替え時に自動的に最新コードを取得できます：

### VS Code / Cursor 設定方法

1. 設定（Settings）を開く: `Ctrl+,`（Win/Linux）または `Cmd+,`（Mac）
2. 「User」タブを選択
3. 検索ボックスに「git.pull」と入力
4. 「Git: Pull Before Checkout」にチェックを入れる
5. 検索ボックスに「git.autofetch」と入力
6. 「Git: Autofetch」にチェックを入れる

または、以下の設定をsettings.jsonに直接追加：

```json
{
  "git.autofetch": true,
  "git.autofetchPeriod": 300,
  "git.pullBeforeCheckout": true
}
```

## 開発ワークフロー

1. 作業開始時：
   ```bash
   git checkout develop
   # 自動的にpullされる
   git checkout -b feature/機能名
   ```

2. 機能実装後：
   ```bash
   git add .
   git commit -m "変更内容を具体的に記述"
   git push -u origin feature/機能名
   ```

3. GitHubでPRを作成
   - テンプレートに従って情報を入力
   - 「重要な変更」に該当する場合はチェックを入れる

4. 必要に応じてレビュー実施

5. PRをマージ（Squash and merge推奨）

6. develop → main へのマージも同様にPR経由で実施

## 保護ブランチへのコミット防止設定（Git Hook）

GitHub上の設定に加えて、ローカル環境でも保護ブランチ（main, develop）への直接コミットを防止するGit Hookを設定できます。この設定は各開発者のマシンで個別に行う必要があります。

### セットアップ手順

リポジトリをクローンした後、以下のコマンドを実行するだけです：

```bash
bash scripts/setup-git-hooks.sh
```

### 効果

- mainとdevelopブランチでは直接コミットができなくなります
- コミット操作をしようとすると、エラーメッセージと対処法が表示されます
- 以下のような操作手順が示されるので、簡単にfeatureブランチに移行できます：

```
1. 変更を退避: git stash
2. 新しいブランチを作成: git checkout -b feature/作業内容
3. 変更を復元: git stash pop
4. 通常通りコミット
```

これにより、「間違ってmainブランチで作業していた」という事故を防ぐことができます。

### 注意点

- このフックは各開発者のローカル環境でのみ有効です
- 新しくリポジトリをクローンした開発者は必ずこのスクリプトを実行する必要があります
- チーム全員がこの保護機能を使うことで、安全な開発フローを維持できます 