#!/bin/bash

echo "🌐 Browser-Enabled Dual-Agent Setup"
echo "=================================="

# 既存セッションの削除
tmux kill-session -t browser-agent1 2>/dev/null
tmux kill-session -t browser-agent2 2>/dev/null

echo "🎯 Browser Agent1セッション作成中..."
tmux new-session -d -s browser-agent1 -c "$(pwd)"
tmux rename-window -t browser-agent1:0 "Browser-Agent1"

echo "🎯 Browser Agent2セッション作成中..."
tmux new-session -d -s browser-agent2 -c "$(pwd)"
tmux rename-window -t browser-agent2:0 "Browser-Agent2"

echo "📦 MCP Browser Serverインストール中..."
if command -v npx >/dev/null 2>&1; then
    echo "npmでインストール中..."
    npx -y @smithery/cli install @JovaniPink/mcp-browser-use --client claude
else
    echo "pipでインストール中..."
    pip install mcp-server-browser-use
fi

echo "✅ セットアップ完了！"
echo ""
echo "📋 使用方法:"
echo "  tmux attach-session -t browser-agent1  # Browser Agent1に接続"
echo "  tmux attach-session -t browser-agent2  # Browser Agent2に接続"
echo ""
echo "🚀 両方のエージェントでClaude + Browser機能を起動:"
echo "  tmux send-keys -t browser-agent1 'claude' C-m"
echo "  tmux send-keys -t browser-agent2 'claude' C-m"
echo ""
echo "🌐 ブラウザタスク例:"
echo "  Agent1: 'ウェブサイトから商品情報を収集してください'"
echo "  Agent2: 'Agent1のデータを分析してレポートを作成してください'"
echo ""
echo "📊 セッション一覧:"
tmux list-sessions 