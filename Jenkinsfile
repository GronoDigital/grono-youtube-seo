pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                sh '''
                echo "📦 Checking out Repository..."
                ls -lah
                '''
            }
        }

        stage('Deploy to EC2') {
            steps {
                sh '''
                echo "🚀 Deploying backend to EC2..."

                # Copy ONLY required backend files
                scp -o StrictHostKeyChecking=no -i /var/lib/jenkins/.ssh/ca2.pem \
                app.py \
                database.py \
                main.py \
                requirements.txt \
                youtube_fetcher.py \
                templates \
                ubuntu@13.61.186.104:/var/www/backend/

                echo "Files uploaded successfully!"
                '''
            }
        }

        stage('Install on EC2') {
            steps {
                sh '''
                echo "⚙ Running remote install..."

                ssh -o StrictHostKeyChecking=no -i /var/lib/jenkins/.ssh/ca2.pem ubuntu@13.61.186.104 "
                    cd /var/www/backend &&
                    python3 -m venv venv &&
                    . venv/bin/activate &&
                    pip install --upgrade pip &&
                    pip install -r requirements.txt &&
                    sudo systemctl restart grono-backend
                "

                echo "Backend deployed & restarted!"
                '''
            }
        }
    }

    post {
        success {
            echo "🎉 Deployment Success!"
        }
        failure {
            echo "❌ Deployment Failed!"
        }
    }
}
