pipeline {

    agent any

    environment {
        // Docker image names
        APP_IMAGE      = "taskflow-app"
        SELENIUM_IMAGE = "taskflow-selenium"
        APP_CONTAINER  = "taskflow-app-ci"
        APP_PORT       = "5000"
        // Unique network per build prevents conflicts on shared Jenkins agents
        DOCKER_NETWORK = "taskflow-net-${BUILD_NUMBER}"
    }

    stages {

        // ── Stage 1: Code Build ──────────────────────────────────────
        stage('Code Build') {
            steps {
                echo '>>> [Stage 1] Installing Python dependencies...'
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install flask flask-sqlalchemy pytest selenium
                '''
                echo '>>> Code Build complete.'
            }
        }

        // ── Stage 2: Unit Testing ────────────────────────────────────
        stage('Unit Testing') {
            steps {
                echo '>>> [Stage 2] Running unit tests with pytest...'
                sh '''
                    . venv/bin/activate
                    python -m pytest test_app.py -v \
                        --tb=short \
                        --junitxml=reports/unit-test-results.xml
                '''
                echo '>>> Unit tests passed.'
            }
            post {
                always {
                    // Publish JUnit test results in Jenkins UI
                    junit allowEmptyResults: true,
                          testResults: 'reports/unit-test-results.xml'
                }
            }
        }

        // ── Stage 3: Containerized Deployment ────────────────────────
        stage('Containerized Deployment') {
            steps {
                echo '>>> [Stage 3] Building and deploying app Docker container...'
                sh '''
                    # Create an isolated Docker network for this build
                    docker network create ${DOCKER_NETWORK}

                    # Build the application image
                    docker build -t ${APP_IMAGE}:${BUILD_NUMBER} \
                                 -t ${APP_IMAGE}:latest \
                                 -f Dockerfile .

                    # Run the app container
                    docker run -d \
                        --name ${APP_CONTAINER} \
                        --network ${DOCKER_NETWORK} \
                        -p ${APP_PORT}:5000 \
                        ${APP_IMAGE}:${BUILD_NUMBER}

                    # Wait until the app is healthy (max 30 s)
                    echo "Waiting for app to be ready..."
                    for i in $(seq 1 15); do
                        if curl -sf http://localhost:${APP_PORT} > /dev/null 2>&1; then
                            echo "App is up after ${i} attempts."
                            break
                        fi
                        sleep 2
                    done

                    # Final health check — fail the build if app never came up
                    curl -sf http://localhost:${APP_PORT} || \
                        (echo "App failed to start!" && exit 1)
                '''
                echo '>>> App container is running and healthy.'
            }
        }

        // ── Stage 4: Containerized Selenium Testing ───────────────────
        stage('Containerized Selenium Testing') {
            steps {
                echo '>>> [Stage 4] Building Selenium image and running browser tests...'
                sh '''
                    mkdir -p reports

                    # Build the Selenium test image
                    docker build -t ${SELENIUM_IMAGE}:${BUILD_NUMBER} \
                                 -f Dockerfile.selenium .

                    # Run Selenium tests inside a container, pointed at the app
                    docker run --rm \
                        --network ${DOCKER_NETWORK} \
                        -e BASE_URL=http://${APP_CONTAINER}:5000 \
                        -v "$(pwd)/reports:/app/reports" \
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

    // ── Post-pipeline cleanup ─────────────────────────────────────────
    post {
        always {
            echo '>>> Cleaning up Docker containers and network...'
            sh '''
                # Stop and remove the app container (ignore errors if already gone)
                docker stop  ${APP_CONTAINER} 2>/dev/null || true
                docker rm    ${APP_CONTAINER} 2>/dev/null || true

                # Remove the per-build network
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
