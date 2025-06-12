#!/bin/bash

echo "🤖 Simple Dual-Agent Setup"
echo "=========================="

# 既存セッションの削除
tmux kill-session -t agent1 2>/dev/null
tmux kill-session -t agent2 2>/dev/null

# Agent1 セッション作成
echo "🎯 Agent1セッション作成中..."
tmux new-session -d -s agent1 -c "$(pwd)"
tmux rename-window -t agent1:0 "Agent1-Claude"

# Agent2 セッション作成
echo "🎯 Agent2セッション作成中..."
tmux new-session -d -s agent2 -c "$(pwd)"
tmux rename-window -t agent2:0 "Agent2-Claude"

echo "✅ セットアップ完了！"
echo ""
echo "📋 使用方法:"
echo "  tmux attach-session -t agent1  # Agent1に接続"
echo "  tmux attach-session -t agent2  # Agent2に接続"
echo ""
echo "🚀 両方のエージェントでClaudeを起動:"
echo "  tmux send-keys -t agent1 'claude' C-m"
echo "  tmux send-keys -t agent2 'claude' C-m"
echo ""
echo "📊 セッション一覧:"
tmux list-sessions 