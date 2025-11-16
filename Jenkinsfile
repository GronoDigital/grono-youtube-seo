pipeline {
    agent any

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', url: https://github.com/GronoDigital/grono-youtube-seo/new/main
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
                ssh -o StrictHostKeyChecking=no ubuntu@<EC2-Public-IP> "sudo rm -rf /var/www/mywebsite/*"
                scp -o StrictHostKeyChecking=no -r build/* ubuntu@<EC2-Public-IP>:/var/www/mywebsite/
                ssh -o StrictHostKeyChecking=no ubuntu@<EC2-Public-IP> "sudo systemctl restart nginx"
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
