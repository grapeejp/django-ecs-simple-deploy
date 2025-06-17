#!/usr/bin/env python
"""
AllowedUserにyasutoshi.yanagimoto@grapee.co.jpを追加するスクリプト
"""
import os
import sys
import django

# Django設定を初期化
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import AllowedUser
from django.contrib.auth.models import User

def main():
    """メイン処理"""
    # yasutoshi.yanagimoto@grapee.co.jp を AllowedUser に追加
    allowed_user, created = AllowedUser.objects.get_or_create(
        email='yasutoshi.yanagimoto@grapee.co.jp',
        defaults={
            'full_name': '柳本安利',
            'department': '開発部',
            'permission_level': 'admin',
            'is_active': True,
            'notes': 'システム管理者'
        }
    )

    if created:
        print(f'AllowedUser作成成功: {allowed_user}')
    else:
        print(f'AllowedUser既存: {allowed_user}')
        # 既存の場合は有効化
        allowed_user.is_active = True
        allowed_user.save()
        print('有効化完了')

    # 既存のDjangoユーザーがいれば関連付け
    try:
        django_user = User.objects.get(email='yasutoshi.yanagimoto@grapee.co.jp')
        allowed_user.django_user = django_user
        allowed_user.save()
        print(f'Djangoユーザーと関連付け完了: {django_user}')
    except User.DoesNotExist:
        print('Djangoユーザーは未作成（OAuth認証時に自動作成されます）')

    print('設定完了！')
    
    # 確認用：AllowedUserの一覧を表示
    print('\n=== 現在のAllowedUser一覧 ===')
    for user in AllowedUser.objects.all():
        print(f'- {user.email}: {user.full_name} ({user.permission_level}) - 有効: {user.is_active}')

if __name__ == '__main__':
    main() 