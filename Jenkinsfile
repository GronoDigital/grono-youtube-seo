pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                sh '''
                echo "📦 Checking out code..."
                pwd
                ls
                '''
            }
        }

        stage('Backend - Install Dependencies') {
            steps {
                sh '''
                echo "🔥 Setting up Python Virtual Env"

                cd /var/lib/jenkins/workspace/gronowork

                # Create venv if not exists
                if [ ! -d "venv" ]; then
                    python3 -m venv venv
                fi

                # Activate venv
                . venv/bin/activate

                # Upgrade pip
                pip install --upgrade pip

                # Install required packages
                pip install -r requirements.txt

                echo "Dependencies Installed Successfully!"
                '''
            }
        }

        stage('Restart Backend Service') {
            steps {
                sh '''
                echo "🔁 Restarting Backend Service..."

                sudo systemctl daemon-reload
                sudo systemctl restart grono-backend
                sudo systemctl status grono-backend --no-pager
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Deployment Successful!"
        }
        failure {
            echo "❌ Deployment Failed!"
        }
    }
}
