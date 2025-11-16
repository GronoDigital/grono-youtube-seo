pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                // Jenkins automatically checks out code, so optionally:
                sh 'pwd && ls'
            }
        }

        stage('Backend - Install Dependencies') {
            steps {
                sh '''
                cd /var/lib/jenkins/workspace/gronowork

                # Create or reuse venv
                if [ ! -d "venv" ]; then
                  python3 -m venv venv
                fi

                . venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Frontend - Build React') {
            steps {
                sh '''
                cd /var/lib/jenkins/workspace/gronowork/frontend

                npm install
                npm run build
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                # Frontend deploy
                rm -rf /var/www/grono_frontend/*
                cp -r /var/lib/jenkins/workspace/gronowork/frontend/build/* /var/www/grono_frontend/

                # Backend restart
                sudo systemctl restart grono-backend
                '''
            }
        }
    }
}
