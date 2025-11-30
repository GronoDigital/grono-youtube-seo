pipeline {
    agent any

    environment {
        AWS_REGION    = 'ap-south-1'
        ACCOUNT_ID    = '460783431753'
        ECR_REPO      = 'grono-youtube-seo'
        CLUSTER       = 'prod-eks-cluster'
        ECR_REGISTRY  = '460783431753.dkr.ecr.ap-south-1.amazonaws.com'
    }

    triggers {
        githubPush()              // Webhook trigger
        pollSCM('H/10 * * * *')   // Backup poll every 10 mins
    }

    stages {

        stage('ECR Login') {
            steps {
                sh '''
                aws ecr get-login-password --region $AWS_REGION \
                | docker login --username AWS --password-stdin $ECR_REGISTRY
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                IMAGE_TAG=$BUILD_NUMBER

                docker build -t $ECR_REPO:$IMAGE_TAG .
                docker tag $ECR_REPO:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPO:$IMAGE_TAG
                docker tag $ECR_REPO:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPO:latest
                '''
            }
        }

        stage('Push to ECR') {
            steps {
                sh '''
                IMAGE_TAG=$BUILD_NUMBER

                docker push $ECR_REGISTRY/$ECR_REPO:$IMAGE_TAG
                docker push $ECR_REGISTRY/$ECR_REPO:latest
                '''
            }
        }

        stage('Deploy to EKS') {
            steps {
                sh '''
                aws eks update-kubeconfig --name $CLUSTER --region $AWS_REGION
                kubectl apply -f k8s/
                '''
            }
        }
    }

    post {
        success {
            echo "✅ CI/CD Pipeline completed successfully"
        }
        failure {
            echo "❌ CI/CD Pipeline failed – check logs"
        }
    }
}
