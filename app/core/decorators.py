from django.contrib.auth.decorators import login_required
from functools import wraps


def admin_login_required(view_func):
    """
    管理者ログイン必須デコレータ
    Django admin のログイン画面にリダイレクトします
    """
    @wraps(view_func)
    @login_required(login_url='/admin/login/')
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper 