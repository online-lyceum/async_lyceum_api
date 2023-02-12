#!groovy

pipeline {
    agent any
    stages {
        stage("Build image") {
            steps {
                sh 'docker build -t time_api:${JOB_NAME} .'
            }
        }
        stage("Run images") {
            steps {
                sh 'docker-compose up -d --remove-orphans'
                sh 'docker-compose exec -d api init_models'
            }
        }
    }
}
