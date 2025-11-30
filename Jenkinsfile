pipeline {
    agent any

    triggers {
        githubPush()
        pollSCM('H/10 * * * *')
    }

    environment {
        AWS_REGION = 'ap-south-1'
        CLUSTER    = 'prod-eks-cluster'
        ECR_REPO   = 'grono-youtube-seo'
    }

    stages {

        stage('ECR Login') {
            steps {
                sh '''
                ACCOUNT_ID=460783431753
                ECR_REGISTRY=$ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com

                aws ecr get-login-password --region ap-south-1 \
                | docker login --username AWS --password-stdin $ECR_REGISTRY
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                ACCOUNT_ID=460783431753
                ECR_REGISTRY=$ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com
                IMAGE_TAG=$BUILD_NUMBER

                docker build --no-cache -t $ECR_REPO:$IMAGE_TAG .
                docker tag $ECR_REPO:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPO:$IMAGE_TAG
                '''
            }
        }

        stage('Push to ECR') {
            steps {
                sh '''
                ACCOUNT_ID=460783431753
                ECR_REGISTRY=$ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com
                IMAGE_TAG=$BUILD_NUMBER

                docker push $ECR_REGISTRY/$ECR_REPO:$IMAGE_TAG
                docker push $ECR_REGISTRY/$ECR_REPO:latest
                '''
            }
        }

        stage('Deploy to EKS') {
            steps {
                sh '''
                aws eks update-kubeconfig --name $CLUSTER --region ap-south-1
                kubectl apply -f k8s/
                kubectl set image deployment/grono-youtube-seo \
                webapp=460783431753.dkr.ecr.ap-south-1.amazonaws.com/grono-youtube-seo:$BUILD_NUMBER
                '''
            }
        }
    }
}

