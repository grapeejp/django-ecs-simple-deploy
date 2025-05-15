from django.test import TestCase, Client
from django.urls import reverse


class TagViewsTest(TestCase):
    """タグ機能のビューをテストするクラス"""
    
    def setUp(self):
        """テスト実行前の準備"""
        self.client = Client()
        self.list_url = reverse('tags:list')  # 'tags:list'のURLを取得
    
    def test_tag_list_GET(self):
        """タグ一覧ページへのGETリクエストが正しく動作するかテスト"""
        response = self.client.get(self.list_url)
        
        # ステータスコードが200（成功）であることを確認
        self.assertEqual(response.status_code, 200)
        
        # 正しいテンプレートが使用されているか確認
        self.assertTemplateUsed(response, 'tags/list.html')
    
    def test_tag_list_POST(self):
        """タグ一覧ページへのPOSTリクエストが正しく動作するかテスト"""
        response = self.client.post(self.list_url, {
            'content': 'テストコンテンツ'
        })
        
        # ステータスコードが200（成功）であることを確認
        self.assertEqual(response.status_code, 200)
        
        # 正しいテンプレートが使用されているか確認
        self.assertTemplateUsed(response, 'tags/list.html')
        
        # POSTリクエスト後にタグが返されることを確認
        self.assertTrue(len(response.context['tags']) > 0) 