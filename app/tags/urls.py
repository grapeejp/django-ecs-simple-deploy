from django.urls import path

app_name = 'tags'

urlpatterns = [
    # 後ほどこの部分に実際のパターンを追加する
    path('', lambda request: None, name='list'),
] 