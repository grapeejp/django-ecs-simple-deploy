from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def tag_list(request):
    """タグ一覧を表示するビュー"""
    tags = []  # 将来的にはデータベースからタグを取得
    
    # POSTリクエストの場合、タグ生成ロジックを実行
    if request.method == 'POST':
        content = request.POST.get('content', '')
        if content:
            # 簡易的なタグ生成（本来はAIモデルなどを使用）
            sample_tags = ['サンプル', 'テスト', 'Django', 'AWS']
            tags = sample_tags
    
    # テンプレートをレンダリングしてHttpResponseを返す
    return render(request, 'tags/list.html', {
        'tags': tags,
    })
