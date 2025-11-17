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

                # Copy python files + db
                scp -o StrictHostKeyChecking=no -i /var/lib/jenkins/.ssh/ca2.pem \
                app.py database.py main.py requirements.txt youtube_fetcher.py youtube_channels.db \
                ubuntu@13.61.186.104:/var/www/backend/

                # Copy templates folder separately
                scp -o StrictHostKeyChecking=no -i /var/lib/jenkins/.ssh/ca2.pem -r templates \
                ubuntu@13.61.186.104:/var/www/backend/

                echo "Files uploaded successfully!"
                '''
            }
        }

        stage('Install on EC2') {
            steps {
                sh '''
                echo "⚙ Installing & Restarting backend on EC2..."

                ssh -o StrictHostKeyChecking=no -i /var/lib/jenkins/.ssh/ca2.pem ubuntu@13.61.186.104 << 'EOF'
                    cd /var/www/backend
                    source venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    sudo systemctl restart grono-backend
                EOF

                echo "Backend deployed & restarted successfully!"
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
