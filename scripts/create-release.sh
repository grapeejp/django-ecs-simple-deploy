#!/bin/bash
# リリースタグ作成スクリプト
# 使用方法: ./create-release.sh [メジャー|マイナー|パッチ] [リリースメッセージ]

set -e

# 色の設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 色リセット

# 現在のディレクトリが git リポジトリのルートか確認
if [ ! -d ".git" ]; then
  echo -e "${RED}エラー: このスクリプトは git リポジトリのルートで実行してください${NC}"
  exit 1
fi

# mainブランチにいることを確認
CURRENT_BRANCH=$(git symbolic-ref --short HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
  echo -e "${YELLOW}警告: 現在 $CURRENT_BRANCH ブランチにいます。リリースは main ブランチから作成すべきです${NC}"
  read -p "続行しますか？ (y/n): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "中止しました"
    exit 1
  fi
fi

# 最新の変更を取得
echo -e "${GREEN}リモートから最新の変更を取得しています...${NC}"
git fetch --tags

# 最新のタグを取得
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo -e "${GREEN}最新のタグ: $LATEST_TAG${NC}"

# バージョン番号を分解
MAJOR=$(echo $LATEST_TAG | sed 's/v\([0-9]*\)\.\([0-9]*\)\.\([0-9]*\)/\1/')
MINOR=$(echo $LATEST_TAG | sed 's/v\([0-9]*\)\.\([0-9]*\)\.\([0-9]*\)/\2/')
PATCH=$(echo $LATEST_TAG | sed 's/v\([0-9]*\)\.\([0-9]*\)\.\([0-9]*\)/\3/')

# リリースタイプを取得
RELEASE_TYPE=${1:-"patch"}
case $RELEASE_TYPE in
  "メジャー"|"major")
    MAJOR=$((MAJOR + 1))
    MINOR=0
    PATCH=0
    ;;
  "マイナー"|"minor")
    MINOR=$((MINOR + 1))
    PATCH=0
    ;;
  "パッチ"|"patch")
    PATCH=$((PATCH + 1))
    ;;
  *)
    echo -e "${RED}エラー: 無効なリリースタイプです。'メジャー'、'マイナー'、'パッチ' のいずれかを指定してください${NC}"
    exit 1
    ;;
esac

# 新しいバージョン番号
NEW_VERSION="v$MAJOR.$MINOR.$PATCH"
echo -e "${GREEN}新しいバージョン: $NEW_VERSION${NC}"

# リリースメッセージの作成
if [ -n "$2" ]; then
  RELEASE_MESSAGE="$2"
else
  # デフォルトメッセージの生成
  echo -e "${YELLOW}リリースメッセージが指定されていません。デフォルトメッセージを生成します${NC}"
  
  # 前回のリリースからのコミットログ取得
  COMMITS=$(git log --pretty=format:"- %s" $LATEST_TAG..HEAD)
  
  # リリースメッセージの雛形
  RELEASE_MESSAGE="# リリース $NEW_VERSION

## 変更内容

$COMMITS

## 既知の問題

なし

## インストール方法

通常の手順に従ってデプロイしてください。"

  # 一時ファイルにリリースメッセージを書き込み
  TMP_FILE=$(mktemp)
  echo "$RELEASE_MESSAGE" > $TMP_FILE
  
  # ユーザーにメッセージの編集を促す
  echo -e "${YELLOW}リリースメッセージを編集します...${NC}"
  ${EDITOR:-vim} $TMP_FILE
  
  # 編集後のメッセージを読み込む
  RELEASE_MESSAGE=$(cat $TMP_FILE)
  rm $TMP_FILE
fi

# 確認
echo -e "${YELLOW}以下の内容でリリースを作成します：${NC}"
echo -e "バージョン: ${GREEN}$NEW_VERSION${NC}"
echo -e "メッセージ:"
echo "$RELEASE_MESSAGE"
echo
read -p "続行しますか？ (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "中止しました"
  exit 1
fi

# タグ作成
echo -e "${GREEN}タグを作成しています...${NC}"
git tag -a $NEW_VERSION -m "$RELEASE_MESSAGE"

# リモートにプッシュ
echo -e "${GREEN}タグをリモートにプッシュしています...${NC}"
git push origin $NEW_VERSION

# GitHub CLIがインストールされている場合はリリースを作成
if command -v gh &> /dev/null; then
  echo -e "${GREEN}GitHub Releaseを作成しています...${NC}"
  echo "$RELEASE_MESSAGE" | gh release create $NEW_VERSION --title "$NEW_VERSION" --notes-file -
fi

echo -e "${GREEN}リリース $NEW_VERSION の作成が完了しました！${NC}"
echo "GitHub Actionsが自動的にデプロイを開始します。進捗を確認するには以下のURLにアクセスしてください："
echo "https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions" 