# Generated by Django 5.2 on 2025-06-16 05:24

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AllowedUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='メールアドレス')),
                ('full_name', models.CharField(max_length=255, verbose_name='氏名')),
                ('department', models.CharField(blank=True, max_length=100, verbose_name='部署')),
                ('permission_level', models.CharField(choices=[('user', '一般ユーザー'), ('admin', '管理者'), ('superuser', 'スーパーユーザー')], default='user', max_length=20, verbose_name='権限レベル')),
                ('is_active', models.BooleanField(default=True, verbose_name='有効')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='最終ログイン')),
                ('notes', models.TextField(blank=True, verbose_name='備考')),
                ('django_user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Djangoユーザー')),
            ],
            options={
                'verbose_name': '認証許可ユーザー',
                'verbose_name_plural': '認証許可ユーザー',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='LoginHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                ('login_time', models.DateTimeField(auto_now_add=True, verbose_name='ログイン時刻')),
                ('ip_address', models.GenericIPAddressField(verbose_name='IPアドレス')),
                ('user_agent', models.TextField(verbose_name='ユーザーエージェント')),
                ('success', models.BooleanField(default=True, verbose_name='成功')),
                ('failure_reason', models.CharField(blank=True, max_length=255, verbose_name='失敗理由')),
                ('session_key', models.CharField(blank=True, max_length=40, verbose_name='セッションキー')),
                ('allowed_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.alloweduser', verbose_name='認証許可ユーザー')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='ユーザー')),
            ],
            options={
                'verbose_name': 'ログイン履歴',
                'verbose_name_plural': 'ログイン履歴',
                'ordering': ['-login_time'],
            },
        ),
        migrations.CreateModel(
            name='UserImportLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                ('file_name', models.CharField(max_length=255, verbose_name='ファイル名')),
                ('total_records', models.IntegerField(verbose_name='総レコード数')),
                ('success_count', models.IntegerField(verbose_name='成功件数')),
                ('error_count', models.IntegerField(verbose_name='エラー件数')),
                ('error_details', models.TextField(blank=True, verbose_name='エラー詳細')),
                ('imported_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='実行者')),
            ],
            options={
                'verbose_name': 'ユーザーインポートログ',
                'verbose_name_plural': 'ユーザーインポートログ',
                'ordering': ['-created_at'],
            },
        ),
    ]
