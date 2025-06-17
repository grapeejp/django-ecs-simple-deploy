from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class TagViewsTest(TestCase):
    """タグ機能のビューをテストするクラス"""
    
    def setUp(self):
        """テスト実行前の準備"""
        self.client = Client()
        self.list_url = reverse('tags:list')  # 'tags:list'のURLを取得
        # テスト用ユーザーを作成
        self.user = User.objects.create_user(
            username='testuser',
            email='test@grapee.co.jp',
            password='testpassword'
        )
    
    def test_tag_list_GET(self):
        """タグ一覧ページへのGETリクエストが正しく動作するかテスト"""
        # ユーザーをログインさせる
        self.client.login(username='testuser', password='testpassword')
        
        response = self.client.get(self.list_url)
        
        # ステータスコードが200（成功）であることを確認
        self.assertEqual(response.status_code, 200)
        
        # 正しいテンプレートが使用されているか確認
        self.assertTemplateUsed(response, 'tags/list.html')
    
    def test_tag_list_POST(self):
        """タグ一覧ページへのPOSTリクエストが正しく動作するかテスト"""
        # ユーザーをログインさせる
        self.client.login(username='testuser', password='testpassword')
        
        response = self.client.post(self.list_url, {
            'content': 'テストコンテンツ'
        })
        
        # ステータスコードが200（成功）であることを確認
        self.assertEqual(response.status_code, 200)
        
        # 正しいテンプレートが使用されているか確認
        self.assertTemplateUsed(response, 'tags/list.html')
        
        # POSTリクエスト後にタグが返されることを確認
        self.assertTrue(len(response.context['tags']) > 0) 