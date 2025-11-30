pipeline {
  agent any

  environment {
    AWS_REGION  = 'ap-south-1'
    ACCOUNT_ID  = '460783431753'
    ECR_REPO    = 'grono-youtube-seo'
    CLUSTER     = 'prod-eks-cluster'
    IMAGE_TAG   = "${BUILD_NUMBER}"
    ECR_REGISTRY = "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
  }

  triggers {
    githubPush()
    pollSCM('H/5 * * * *')
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('ECR Login') {
      steps {
        sh '''
          aws ecr get-login-password --region $AWS_REGION | \
            docker login --username AWS --password-stdin \
            $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
        '''
      }
    }

    stage('Build Docker Image') {
      steps {
        sh """
          docker build -t $ECR_REPO:$IMAGE_TAG .
          docker tag $ECR_REPO:$IMAGE_TAG \
             IMAGE = "${ECR_REGISTRY}/repo:latest"

#            $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
        """
      }
    }

    stage('Push to ECR') {
      steps {
        sh """
          docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG
          docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
        """
      }
    }

    stage('Deploy to EKS') {
      steps {
        sh """
          aws eks update-kubeconfig --name $CLUSTER --region $AWS_REGION
          kubectl apply -f k8s/deployment.yaml
          kubectl apply -f k8s/service.yaml
        """
      }
    }
  }

  post {
    success {
      echo "Deployment successful!"
    }
    failure {
      echo "Deployment failed! Check logs."
    }
  }
}
