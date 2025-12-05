1. first create a virtual environment
2. navigate to ecommerce-platform
3. run python -m pip install -r  requirements.txt
4. run redis container in docker
5. migrate all migrations
6. create .env file
   EMAIL_PORT=465
  EMAIL_HOST_USER="abc@gmail.com"
  EMAIL_HOST_PASSWORD="app_password"
  KEY_ID="razorpay_key_id"
  KEY_SECRET="rezorpay_secret_id"
  WEBHOOK_SECRET=razorpay_webhook_secret

8. a) open ngrok and create a tunnel for the port 8000. and paste the public url in django's setting.py
   ALLOWED_HOSTS = ["127.0.0.1","localhost","ngrok-public-url without https"]
  CSRF_TRUSTED_ORIGINS = [
    "ngrok-pubic-url",
]
  b) paste the ngrok-link in webhook-url in razorpya webhook.


9. run python manage.py runserver