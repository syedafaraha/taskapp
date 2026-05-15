pipeline {

    agent any

    environment {
        APP_IMAGE      = "taskflow-app"
        SELENIUM_IMAGE = "taskflow-selenium"
        APP_CONTAINER  = "taskflow-app-ci"
        APP_PORT       = "5000"
        DOCKER_NETWORK = "taskflow-net-${BUILD_NUMBER}"
    }

    stages {

        stage('Code Build') {
            steps {
                echo '>>> [Stage 1] Installing Python dependencies...'
                sh '''
                    docker run --rm \
                        -v "$(pwd)":/app \
                        -w /app \
                        python:3.11-slim \
                        pip install flask flask-sqlalchemy pytest selenium --quiet
                '''
                echo '>>> Code Build complete.'
            }
        }

        stage('Unit Testing') {
            steps {
                echo '>>> [Stage 2] Running unit tests inside Docker...'
                sh '''
                    mkdir -p reports
                    cat > /tmp/run_tests.sh << SCRIPT
pip install flask flask-sqlalchemy pytest --quiet
python -m pytest test_app.py -v --tb=short --junitxml=/app/reports/unit-test-results.xml
SCRIPT
                    docker run --rm \
                        -v "$(pwd)":/app \
                        -v /tmp/run_tests.sh:/run_tests.sh \
                        -w /app \
                        python:3.11-slim \
                        sh /run_tests.sh
                '''
                echo '>>> Unit tests passed.'
            }
            post {
                always {
                    junit allowEmptyResults: true,
                          testResults: 'reports/unit-test-results.xml'
                }
            }
        }

        stage('Containerized Deployment') {
            steps {
                echo '>>> [Stage 3] Building and deploying app Docker container...'
                sh '''
                    docker network create ${DOCKER_NETWORK}

                    docker build -t ${APP_IMAGE}:${BUILD_NUMBER} \
                                 -t ${APP_IMAGE}:latest \
                                 -f Dockerfile .

                    docker run -d \
                        --name ${APP_CONTAINER} \
                        --network ${DOCKER_NETWORK} \
                        -p ${APP_PORT}:5000 \
                        ${APP_IMAGE}:${BUILD_NUMBER}

                    echo "Waiting for app to be ready..."
                    for i in $(seq 1 15); do
                        if docker exec ${APP_CONTAINER} curl -sf http://localhost:5000 > /dev/null 2>&1; then
                            echo "App is up after ${i} attempts."
                            break
                        fi
                        sleep 2
                    done

                    docker exec ${APP_CONTAINER} curl -sf http://localhost:5000 || \
                        (echo "App failed to start!" && exit 1)
                '''
                echo '>>> App container is running and healthy.'
            }
        }

        stage('Containerized Selenium Testing') {
            steps {
                echo '>>> [Stage 4] Running Selenium tests...'
                sh '''
                    mkdir -p reports

                    docker build -t ${SELENIUM_IMAGE}:${BUILD_NUMBER} \
                                 -f Dockerfile.selenium .

                    docker run --rm \
                        --network ${DOCKER_NETWORK} \
                        -e BASE_URL=http://${APP_CONTAINER}:5000 \
                        -v "$(pwd)/reports":/app/reports \
                        ${SELENIUM_IMAGE}:${BUILD_NUMBER} \
                        python -m pytest test_selenium.py -v \
                            --tb=short \
                            --junitxml=/app/reports/selenium-test-results.xml
                '''
                echo '>>> Selenium tests passed.'
            }
            post {
                always {
                    junit allowEmptyResults: true,
                          testResults: 'reports/selenium-test-results.xml'
                }
            }
        }
    }

    post {
        always {
            echo '>>> Cleaning up Docker containers and network...'
            sh '''
                docker stop  ${APP_CONTAINER} 2>/dev/null || true
                docker rm    ${APP_CONTAINER} 2>/dev/null || true
                docker network rm ${DOCKER_NETWORK} 2>/dev/null || true
            '''
        }
        success {
            echo "✅ Pipeline SUCCESS — Build #${BUILD_NUMBER} deployed and tested."
        }
        failure {
            echo "❌ Pipeline FAILED — Check the logs above for details."
        }
    }
}
