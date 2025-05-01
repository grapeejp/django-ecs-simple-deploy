from django.http import JsonResponse


def health_check(request):
    """
    ALBのヘルスチェック用エンドポイント
    """
    return JsonResponse({"status": "healthy"}, status=200)
