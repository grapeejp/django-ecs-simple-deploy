FROM nginx:alpine

# Basic認証用のパスワードファイルをコピー
COPY .htpasswd_staging /etc/nginx/.htpasswd_staging
COPY .htpasswd_production /etc/nginx/.htpasswd_production

# nginx設定ファイルをコピー
COPY nginx.conf /etc/nginx/nginx.conf

# ログディレクトリの作成
RUN mkdir -p /var/log/nginx

# nginx実行
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"] 