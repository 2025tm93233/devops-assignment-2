pipeline {
    agent any

    environment {
        IMAGE_NAME = 'aceest-fitness'
    }

    stages {
        stage('Run unit tests') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'python3 -m unittest discover -s . -p "test_*.py" -v'
                    } else {
                        bat 'py -3 -m unittest discover -s . -p "test_*.py" -v'
                    }
                }
            }
        }

        stage('Build Docker image') {
            steps {
                script {
                    if (isUnix()) {
                        sh "docker build --tag ${env.IMAGE_NAME}:${env.BUILD_NUMBER} --tag ${env.IMAGE_NAME}:latest ."
                    } else {
                        bat "docker build --tag ${env.IMAGE_NAME}:${env.BUILD_NUMBER} --tag ${env.IMAGE_NAME}:latest ."
                    }
                }
            }
        }

        stage('Deploy with rollback') {
            steps {
                script {
                    def deployCommand = "kubectl apply -f kubernetes.yaml"
                    def verifyCommand = "kubectl rollout status deployment/aceest-fitness --timeout=120s"
                    def rollbackCommand = "kubectl rollout undo deployment/aceest-fitness"

                    if (isUnix()) {
                        sh(deployCommand)
                        try {
                            sh(verifyCommand)
                        } catch (Exception rolloutFailure) {
                            sh(rollbackCommand)
                            sh(verifyCommand)
                            error("Deployment failed and was rolled back to the previous stable revision")
                        }
                    } else {
                        bat(deployCommand)
                        try {
                            bat(verifyCommand)
                        } catch (Exception rolloutFailure) {
                            bat(rollbackCommand)
                            bat(verifyCommand)
                            error("Deployment failed and was rolled back to the previous stable revision")
                        }
                    }
                }
            }
        }
    }
}
