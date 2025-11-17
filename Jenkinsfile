pipeline {
    agent any

    environment {
        EC2_IP = "13.61.186.104"
        EC2_USER = "ubuntu"
        SSH_KEY = "~/.ssh/ca2.pem"
        BACKEND_DIR = "/var/www/backend"
    }

    stages {

        stage('Checkout') {
            steps {
                sh '''
                echo "📦 Checking out Repository..."
                pwd
                ls -lah
                '''
            }
        }

        stage('Backend Setup') {
            steps {
                sh '''
                echo "🔥 Setting up Python virtual environment..."

                cd $WORKSPACE

                # Create venv if not exists
                if [ ! -d "venv" ]; then
                    echo "⚙ Creating virtual environment..."
                    python3 -m venv venv
                fi

                echo "⚙ Activating venv..."
                . venv/bin/activate

                echo "⬆ Upgrading pip..."
                pip install --upgrade pip

                echo "📦 Installing requirements..."
                pip install -r requirements.txt

                echo "🏁 Backend setup complete!"
                '''
            }
        }

        stage('Deploy to EC2') {
            steps {
                sh '''
                echo "🚀 Deploying backend to EC2..."

                # Copy project files to EC2 server
                scp -o StrictHostKeyChecking=no -i $SSH_KEY -r $WORKSPACE/* $EC2_USER@$EC2_IP:$BACKEND_DIR/

                echo "🔁 Restarting backend service on EC2..."
                ssh -o StrictHostKeyChecking=no -i $SSH_KEY $EC2_USER@$EC2_IP "sudo systemctl restart backend"

                echo "🎉 Deployment Completed Successfully!"
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline executed successfully!"
        }
        failure {
            echo "❌ Deployment Failed!"
        }
    }
}
