# Generated by Django 5.2 on 2025-05-28 06:56

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proofreading_ai', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyDictionary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('term', models.CharField(max_length=255, verbose_name='用語')),
                ('correct_form', models.CharField(max_length=255, verbose_name='正式表記')),
                ('alternative_forms', models.TextField(blank=True, help_text='カンマ区切りで複数指定可能', verbose_name='代替表記')),
                ('category', models.CharField(choices=[('general', '一般用語'), ('brand', 'ブランド名'), ('product', '製品名'), ('department', '部署名'), ('title', '役職名'), ('technical', '技術用語'), ('business', 'ビジネス用語')], default='general', max_length=50, verbose_name='カテゴリー')),
                ('description', models.TextField(blank=True, verbose_name='説明')),
                ('usage_example', models.TextField(blank=True, verbose_name='使用例')),
                ('is_active', models.BooleanField(default=True, verbose_name='有効')),
                ('priority', models.IntegerField(default=1, help_text='数値が大きいほど優先度が高い', verbose_name='優先度')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
            ],
            options={
                'verbose_name': '社内辞書',
                'verbose_name_plural': '社内辞書',
                'ordering': ['-priority', 'term'],
            },
        ),
        migrations.CreateModel(
            name='CorrectionV2',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_text', models.CharField(max_length=500, verbose_name='修正前テキスト')),
                ('corrected_text', models.CharField(max_length=500, verbose_name='修正後テキスト')),
                ('reason', models.TextField(verbose_name='修正理由')),
                ('category', models.CharField(choices=[('tone', '言い回しアドバイス'), ('typo', '誤字修正'), ('dict', '社内辞書ルール'), ('geo', '地域矛盾チェック')], max_length=10, verbose_name='カテゴリー')),
                ('confidence', models.FloatField(help_text='0.0-1.0の範囲', verbose_name='信頼度')),
                ('position', models.IntegerField(help_text='元テキスト内での開始位置', verbose_name='文字位置')),
                ('severity', models.CharField(choices=[('high', '高'), ('medium', '中'), ('low', '低')], default='medium', max_length=10, verbose_name='重要度')),
                ('is_applied', models.BooleanField(default=False, verbose_name='適用済み')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='作成日時')),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='corrections_v2', to='proofreading_ai.proofreadingrequest')),
            ],
            options={
                'verbose_name': '校正修正v2',
                'verbose_name_plural': '校正修正v2',
                'ordering': ['position'],
            },
        ),
        migrations.CreateModel(
            name='GeographicData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='名称')),
                ('type', models.CharField(choices=[('prefecture', '都道府県'), ('city', '市区町村'), ('region', '地域'), ('landmark', 'ランドマーク')], max_length=20, verbose_name='種別')),
                ('latitude', models.FloatField(blank=True, null=True, verbose_name='緯度')),
                ('longitude', models.FloatField(blank=True, null=True, verbose_name='経度')),
                ('climate_zone', models.CharField(blank=True, max_length=50, verbose_name='気候区分')),
                ('characteristics', models.TextField(blank=True, help_text='気候や地理的特徴など', verbose_name='特徴')),
                ('is_active', models.BooleanField(default=True, verbose_name='有効')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='作成日時')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='proofreading_ai.geographicdata', verbose_name='親地域')),
            ],
            options={
                'verbose_name': '地理データ',
                'verbose_name_plural': '地理データ',
                'ordering': ['type', 'name'],
            },
        ),
    ]
