pipeline {
    agent any

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', url: 'https://github.com/GronoDigital/grono-youtube-seo.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'npm install'
            }
        }

        stage('Build Project') {
            steps {
                sh 'npm run build'
            }
        }

        stage('Deploy to EC2') {
            steps {
                sh '''
                ssh -o StrictHostKeyChecking=no ubuntu@13.61.186.104 "sudo rm -rf /var/www/mywebsite/*"
                scp -o StrictHostKeyChecking=no -r build/* ubuntu@13.61.186.104:/var/www/mywebsite/
                ssh -o StrictHostKeyChecking=no ubuntu@13.61.186.104 "sudo systemctl restart nginx"
                '''
            }
        }
    }

    post {
        success {
            echo "Deployment Successful!"
        }
        failure {
            echo "Deployment Failed!"
        }
    }
}

