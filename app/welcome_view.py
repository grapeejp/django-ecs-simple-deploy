from django.http import HttpResponse


def welcome(request):
    """
    シンプルなウェルカムページを表示するビュー
    """
    html = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Django ECS Simple Deploy</title>
        <style>
            body {
                font-family: 'Helvetica Neue', Arial, sans-serif;
                background: #f5f7fa;
                color: #333;
                line-height: 1.6;
                padding: 0;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 2rem;
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                text-align: center;
            }
            h1 {
                color: #2d3748;
                margin-bottom: 0.5rem;
            }
            .subtitle {
                color: #4a5568;
                margin-bottom: 2rem;
            }
            .success {
                background-color: #d4edda;
                color: #155724;
                padding: 1rem;
                border-radius: 5px;
                margin-bottom: 2rem;
            }
            .info {
                background-color: #e7f5ff;
                color: #0c5460;
                padding: 1rem;
                border-radius: 5px;
                text-align: left;
                margin-bottom: 1rem;
            }
            code {
                background: #edf2f7;
                padding: 0.2rem 0.4rem;
                border-radius: 3px;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Django ECS Simple Deploy</h1>
            <p class="subtitle">AWS ECSでDjangoアプリケーションを簡単にデプロイするプロジェクト</p>
            
            <div class="success">
                <strong>成功！</strong> Djangoアプリケーションが正常に動作しています。
            </div>
            
            <div class="info">
                <h3>アプリケーション:</h3>
                <ul>
                    <li><a href="/dashboard/" style="color: #0c5460; text-decoration: none; font-weight: bold;">📊 ダッシュボード</a> - メインアプリケーション</li>
                    <li><a href="/accounts/login/" style="color: #0c5460; text-decoration: none; font-weight: bold;">🔐 ログイン</a> - Google Workspace認証</li>
                    <li><a href="/admin/" style="color: #0c5460; text-decoration: none; font-weight: bold;">⚙️ 管理画面</a> - システム管理</li>
                    <li><a href="/health/" style="color: #0c5460; text-decoration: none; font-weight: bold;">💚 ヘルスチェック</a> - システム状態確認</li>
                </ul>
            </div>
            
            <div class="info">
                <h3>デプロイ情報:</h3>
                <ul>
                    <li>AWSアカウント情報を<code>.env</code>ファイルに設定</li>
                    <li>ECRにDockerイメージをプッシュ</li>
                    <li>CloudFormationスタックをデプロイ</li>
                    <li>ALB経由でアプリケーションにアクセス</li>
                </ul>
            </div>
            
            <p>詳細な手順は<code>DEPLOY.md</code>ファイルを参照してください。</p>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)
