# user_data.sh - EC2 initialization script
#!/bin/bash
set -e

# Update system
yum update -y

# Install Docker
amazon-linux-extras install docker -y
systemctl start docker
systemctl enable docker

# Install docker-compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install nginx (as a backup)
amazon-linux-extras install nginx1 -y

# Create application directory
mkdir -p /opt/webapp

# Create a simple HTML file (backup if Docker fails)
cat > /opt/webapp/app.html <<EOF
<!DOCTYPE html>
<html>
<head>
    <title>DevOps Demo - ${environment}</title>
</head>
<body>
    <h1>DevOps Demo Application</h1>
    <p>Environment: ${environment}</p>
    <p>Instance: $(ec2-metadata --instance-id | cut -d " " -f 2)</p>
    <p>Region: $(ec2-metadata --availability-zone | cut -d " " -f 2 | sed 's/.$//')</p>
</body>
</html>
EOF

# Configure nginx
cat > /etc/nginx/conf.d/webapp.conf <<EOF
server {
    listen 80;
    server_name _;
    
    location / {
        root /opt/webapp;
        index app.html;
    }
    
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Start nginx
systemctl start nginx
systemctl enable nginx

# Add CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Log completion
echo "User data script completed at $(date)" >> /var/log/user-data.log
