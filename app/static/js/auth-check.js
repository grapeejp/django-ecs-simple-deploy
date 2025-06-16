// 認証状態チェック（キャッシュ無効化対応）
document.addEventListener('DOMContentLoaded', function() {
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
            // 認証されていない場合は即座にリダイレクト
            const currentPath = window.location.pathname;
            const loginUrl = `/accounts/login/?next=${encodeURIComponent(currentPath)}`;
            
            console.log('User not authenticated, redirecting to:', loginUrl);
            window.location.href = loginUrl;
        } else {
            console.log('User authenticated:', data.user);
        }
    })
    .catch(error => {
        console.error('Auth check failed:', error);
        // エラーの場合も安全のためログインページにリダイレクト
        const currentPath = window.location.pathname;
        const loginUrl = `/accounts/login/?next=${encodeURIComponent(currentPath)}`;
        window.location.href = loginUrl;
    });
}); 