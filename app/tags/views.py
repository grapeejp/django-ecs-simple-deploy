from django.shortcuts import render

# Create your views here.
def tag_list(request):
    """タグ一覧を表示するビュー"""
    return render(request, 'tags/list.html', {
        'tags': [],  # 将来的にはデータベースからタグを取得
    })
