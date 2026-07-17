aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 105519505372.dkr.ecr.us-east-1.amazonaws.com

docker build -t cpp-ecr-x24244228:latest .

docker tag cpp-ecr-x24244228:latest 105519505372.dkr.ecr.us-east-1.amazonaws.com/cpp-ecr-x24244228:latest

docker push 105519505372.dkr.ecr.us-east-1.amazonaws.com/cpp-ecr-x24244228:latest