// 認証状態チェック（キャッシュ無効化対応）
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    
    // ログインページや公開ページでは認証チェックをスキップ
    const publicPaths = ['/accounts/login/', '/accounts/signup/', '/accounts/logout/', '/'];
    if (publicPaths.some(path => currentPath.includes(path))) {
        console.log('Skipping auth check - on public page');
        return;
    }
    
    // セッションストレージでチェック済みフラグを確認
    const authChecked = sessionStorage.getItem('authChecked');
    if (authChecked === 'true') {
        console.log('Auth already checked in this session');
        return;
    }
    
    // キャッシュ無効化のためのタイムスタンプ追加
    const timestamp = new Date().getTime();
    const authCheckUrl = `/dashboard/api/auth-status/?t=${timestamp}`;
    
    fetch(authCheckUrl, {
        method: 'GET',
        headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        },
        cache: 'no-store'  // ブラウザキャッシュ完全無効化
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Auth check result:', data);
        
        if (!data.authenticated) {
            // 認証されていない場合
            if (data.error && data.error.includes('not in allowed list')) {
                // 許可リストにないユーザーの場合はエラーメッセージを表示
                alert('このアカウントはシステムへのアクセスが許可されていません。管理者にお問い合わせください。');
            }
            
            // セッションストレージをクリア
            sessionStorage.removeItem('authChecked');
            
            // ログインページにリダイレクト
            const loginUrl = `/accounts/login/?next=${encodeURIComponent(currentPath)}`;
            console.log('User not authenticated, redirecting to:', loginUrl);
            window.location.href = loginUrl;
        } else {
            // 認証成功時はフラグを設定
            sessionStorage.setItem('authChecked', 'true');
            console.log('User authenticated:', data.user);
        }
    })
    .catch(error => {
        console.error('Auth check failed:', error);
        // エラーの場合も安全のためログインページにリダイレクト
        sessionStorage.removeItem('authChecked');
        const loginUrl = `/accounts/login/?next=${encodeURIComponent(currentPath)}`;
        window.location.href = loginUrl;
    });
}); 