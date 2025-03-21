#!/bin/bash

if [ "$(id -u)" -ne "0" ]; then
  echo "This script must be run as root."
  exit 1
fi

if [ -f api-core.env ]; then
  echo "Loading environment variables from api-core.env..."
  export $(cat api-core.env | grep -v '#' | xargs)
else
  echo "api-core.env file not found! Please ensure it contains DOMAIN and EMAIL."
  exit 1
fi

if [ -z "$DOMAIN" ]; then
  echo "DOMAIN environment variable is not set."
  exit 1
fi

if [ -z "$EMAIL" ]; then
  echo "EMAIL environment variable is not set."
  exit 1
fi

echo "Installing Nginx and Certbot..."
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx

systemctl start nginx
systemctl enable nginx

echo "Configuring Nginx for your domain..."
envsubst < ./nginx_template.conf > /etc/nginx/sites-available/$DOMAIN

ln -s /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/

nginx -t

systemctl reload nginx

echo "Obtaining SSL certificate from Let's Encrypt..."
certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --no-eff-email

echo "Setting up auto-renewal for Let's Encrypt SSL..."
echo "0 0 * * * root certbot renew --quiet && systemctl reload nginx" > /etc/cron.d/certbot-renew

systemctl restart nginx

echo "SSL configuration with Let's Encrypt is complete!"
echo "Your website is now accessible at https://$DOMAIN"