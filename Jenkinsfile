pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                sh '''
                echo "📦 Checking out code..."
                pwd
                ls -lah
                '''
            }
        }

        stage('Backend Setup') {
            steps {
                sh '''
                echo "🔥 Setting up virtual environment..."

                cd /var/lib/jenkins/workspace/gronowork

                # Fix permissions
                sudo chown -R jenkins:jenkins /var/lib/jenkins/workspace/gronowork

                # Create virtual environment if missing
                if [ ! -d "venv" ]; then
                    python3 -m venv venv
                fi

                # Activate venv
                . venv/bin/activate

                # Update pip
                pip install --upgrade pip

                # Install backend packages
                pip install -r requirements.txt

                echo "Dependencies installation complete!"
                '''
            }
        }

        stage('Restart Backend Service') {
            steps {
                sh '''
                echo "🔁 Restarting backend service..."

                # Allow Jenkins to restart systemd service
                echo "jenkins ALL=(ALL) NOPASSWD: /bin/systemctl restart grono-backend" | sudo tee /etc/sudoers.d/jenkins

                sudo systemctl daemon-reload
                sudo systemctl restart grono-backend
                sudo systemctl status grono-backend --no-pager

                echo "Backend restarted!"
                '''
            }
        }
    }

    post {
        success {
            echo "🎉 Deployment Success — Website Updated!"
        }
        failure {
            echo "❌ Deployment Failed!"
        }
    }
}

