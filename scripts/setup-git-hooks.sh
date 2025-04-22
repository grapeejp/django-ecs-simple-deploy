#!/bin/bash

# 保護ブランチへの直接コミットを防止するGit Hookをセットアップするスクリプト
# 使用方法: bash scripts/setup-git-hooks.sh
# 実行すると、main/developブランチへの直接コミットができなくなります

# カラーコード
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}保護ブランチ（main, develop）へのコミット防止フックをセットアップします...${NC}"

# Git Hooksディレクトリがない場合は作成
if [ ! -d ".git/hooks" ]; then
  mkdir -p .git/hooks
  echo -e "${GREEN}.git/hooks ディレクトリを作成しました${NC}"
fi

# pre-commit hookの内容
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# 現在のブランチ名を取得
branch="$(git rev-parse --abbrev-ref HEAD)"

# 保護されたブランチリスト
protected_branches=("main" "develop")

# 現在のブランチが保護ブランチかチェック
for protected_branch in "${protected_branches[@]}"; do
  if [ "$branch" = "$protected_branch" ]; then
    echo -e "\033[0;31mエラー: $branch ブランチには直接コミットできません！\033[0m"
    echo -e "\033[1;33m対処法:\033[0m"
    echo "1. 変更を退避: git stash"
    echo "2. 新しいブランチを作成: git checkout -b feature/作業内容"
    echo "3. 変更を復元: git stash pop"
    echo "4. 通常通りコミット"
    echo ""
    echo -e "\033[0;32mヒント: 以下のコマンドを実行すると一連の操作を自動で行います\033[0m"
    echo "git stash && git checkout -b feature/my-work && git stash pop"
    exit 1
  fi
done

exit 0
EOF

# 実行権限を付与
chmod +x .git/hooks/pre-commit

echo -e "${GREEN}セットアップ完了！${NC}"
echo -e "これで main または develop ブランチに直接コミットしようとすると自動的に防止されます"
echo -e "${YELLOW}注意: このフックは現在のリポジトリにのみ適用されます${NC}"
echo -e "すべての開発者は各自のマシンでこのスクリプトを実行する必要があります:"
echo -e "${GREEN}bash scripts/setup-git-hooks.sh${NC}" 