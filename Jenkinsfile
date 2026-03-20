pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  parameters {
    string(name: 'GIT_REF', defaultValue: 'main', description: 'Branch, tag, or commit to checkout')
    string(name: 'DOCKER_REGISTRY', defaultValue: 'docker.io', description: 'Docker registry hostname')
    string(name: 'DOCKER_IMAGE', defaultValue: 'rkdevops04/flask-app', description: 'Docker image name (without registry)')
    string(name: 'DOCKER_TAG', defaultValue: '', description: 'Override Docker tag. Empty = build number + short sha')
    string(name: 'BLACKDUCK_URL', defaultValue: 'https://blackduck.example.com', description: 'Black Duck server URL')
    string(name: 'VERACODE_SCAN_JAR', defaultValue: 'pipeline-scan.jar', description: 'Path to Veracode Pipeline Scan jar on the Jenkins agent')
    string(name: 'SYSDIG_API_URL', defaultValue: 'https://secure.sysdig.com', description: 'Sysdig Secure API URL')
    booleanParam(name: 'PUSH_GIT_TAG', defaultValue: false, description: 'Push git tag to origin')
    booleanParam(name: 'PUBLISH_DOCKER_IMAGE', defaultValue: false, description: 'Push Docker image to registry')
    booleanParam(name: 'RUN_SONAR', defaultValue: false, description: 'Run Sonar scan and quality gate')
    booleanParam(name: 'RUN_BLACKDUCK', defaultValue: false, description: 'Run Black Duck scan')
    booleanParam(name: 'RUN_VERACODE', defaultValue: false, description: 'Run Veracode scan')
    booleanParam(name: 'RUN_SYSDIG', defaultValue: false, description: 'Run Sysdig image scan')
  }

  environment {
    PYTHONUNBUFFERED = '1'
    VENV_DIR = '.venv'
    SONARQUBE_ENV_NAME = 'sonarqube'
    SONAR_PROJECT_KEY = 'py-grafana-docker'
  }

  stages {
    stage('checkout scm') {
      steps {
        checkout scm
      }
    }

    stage('git checkout') {
      steps {
        sh 'git fetch --all --tags --prune'
        sh 'git checkout "${GIT_REF}"'
      }
    }

    stage('pre-flight') {
      steps {
        sh '''#!/usr/bin/env bash
          set -euo pipefail
          command -v python3
          command -v pip3
          command -v docker
          python3 --version
          pip3 --version
          docker --version
        '''
      }
    }

    stage('run pipeline') {
      steps {
        sh 'echo "Starting pipeline for ${JOB_NAME} #${BUILD_NUMBER} on ${GIT_REF}"'
        sh 'git rev-parse --short HEAD'
      }
    }

    stage('prepare') {
      steps {
        sh '''#!/usr/bin/env bash
          set -euo pipefail
          python3 -m venv "${VENV_DIR}"
          . "${VENV_DIR}/bin/activate"
          python -m pip install --upgrade pip
          pip install -r requirements.txt
        '''
      }
    }

    stage('validate') {
      steps {
        sh '''#!/usr/bin/env bash
          set -euo pipefail
          . "${VENV_DIR}/bin/activate"
          python -m py_compile app.py
          pip check
        '''
      }
    }

    stage('build') {
      steps {
        sh '''#!/usr/bin/env bash
          set -euo pipefail
          mkdir -p build
          tar -czf build/source-${BUILD_NUMBER}.tar.gz app.py requirements.txt tests Dockerfile docker-compose.yml
        '''
      }
    }

    stage('unit tests') {
      steps {
        sh '''#!/usr/bin/env bash
          set -euo pipefail
          mkdir -p reports
          . "${VENV_DIR}/bin/activate"
          pytest -q --junitxml=reports/junit.xml
        '''
      }
      post {
        always {
          junit 'reports/junit.xml'
        }
      }
    }

    stage('sonar qualityGate') {
      when {
        expression { return params.RUN_SONAR && env.SONARQUBE_ENV_NAME?.trim() && env.SONAR_PROJECT_KEY?.trim() }
      }
      steps {
        withSonarQubeEnv("${SONARQUBE_ENV_NAME}") {
          sh '''#!/usr/bin/env bash
            set -euo pipefail
            sonar-scanner \
              -Dsonar.projectKey="${SONAR_PROJECT_KEY}" \
              -Dsonar.projectName="py-grafana-docker" \
              -Dsonar.sources=. \
              -Dsonar.python.version=3.9
          '''
        }
      }
      post {
        success {
          timeout(time: 10, unit: 'MINUTES') {
            waitForQualityGate abortPipeline: true
          }
        }
      }
    }

    stage('parallel scurtiy scans') {
      parallel {
        stage('blackduck scan') {
          steps {
            script {
              if (params.RUN_BLACKDUCK) {
                withCredentials([string(credentialsId: 'blackduck-api-token', variable: 'BLACKDUCK_API_TOKEN')]) {
                  sh '''#!/usr/bin/env bash
                    set -euo pipefail
                    command -v curl >/dev/null
                    echo "Running Black Duck Detect scan against ${BLACKDUCK_URL}"
                    bash <(curl -s -L https://detect.blackduck.com/detect10.sh) \
                      --blackduck.url="${BLACKDUCK_URL}" \
                      --blackduck.api.token="${BLACKDUCK_API_TOKEN}" \
                      --detect.project.name="py-grafana-docker" \
                      --detect.project.version.name="${GIT_REF}-${BUILD_NUMBER}" \
                      --detect.source.path="${WORKSPACE}"
                  '''
                }
              } else {
                echo 'Skipping Black Duck scan (RUN_BLACKDUCK=false)'
              }
            }
          }
        }
        stage('veracode scan') {
          steps {
            script {
              if (params.RUN_VERACODE) {
                withCredentials([
                  string(credentialsId: 'veracode-api-id', variable: 'VERACODE_API_ID'),
                  string(credentialsId: 'veracode-api-key', variable: 'VERACODE_API_KEY')
                ]) {
                  sh '''#!/usr/bin/env bash
                    set -euo pipefail
                    command -v java >/dev/null
                    test -f "${VERACODE_SCAN_JAR}"
                    echo "Running Veracode scan"
                    java -jar "${VERACODE_SCAN_JAR}" \
                      -vid "${VERACODE_API_ID}" \
                      -vkey "${VERACODE_API_KEY}" \
                      -f "build/source-${BUILD_NUMBER}.tar.gz" \
                      --fail_on_severity="Very High,High"
                  '''
                }
              } else {
                echo 'Skipping Veracode scan (RUN_VERACODE=false)'
              }
            }
          }
        }
      }
    }

    stage('package') {
      steps {
        sh '''#!/usr/bin/env bash
          set -euo pipefail
          mkdir -p dist
          cp build/source-${BUILD_NUMBER}.tar.gz dist/
        '''
      }
    }

    stage('sysdig') {
      steps {
        script {
          if (params.RUN_SYSDIG) {
            withCredentials([string(credentialsId: 'sysdig-secure-api-token', variable: 'SYSDIG_SECURE_API_TOKEN')]) {
              sh '''#!/usr/bin/env bash
                set -euo pipefail
                command -v sysdig-cli-scanner >/dev/null
                echo "Running Sysdig source scan"
                sysdig-cli-scanner \
                  --apiurl "${SYSDIG_API_URL}" \
                  --apitoken "${SYSDIG_SECURE_API_TOKEN}" \
                  --console-log \
                  "dir:${WORKSPACE}"
              '''
            }
          } else {
            echo 'Skipping Sysdig scan (RUN_SYSDIG=false)'
          }
        }
      }
    }

    stage('publish') {
      steps {
        archiveArtifacts artifacts: 'dist/*.tar.gz', fingerprint: true
      }
    }

    stage('tag artifact') {
      steps {
        script {
          env.ARTIFACT_TAG = "build-${BUILD_NUMBER}"
          sh 'git tag -a "${ARTIFACT_TAG}" -m "Jenkins build ${BUILD_NUMBER}" || true'
          if (params.PUSH_GIT_TAG) {
            sh 'git push origin "${ARTIFACT_TAG}"'
          } else {
            echo 'Skipping git tag push (PUSH_GIT_TAG=false)'
          }
        }
      }
    }

    stage('verfication') {
      steps {
        sh '''#!/usr/bin/env bash
          set -euo pipefail
          test -f "dist/source-${BUILD_NUMBER}.tar.gz"
          echo "Verification complete: package exists"
        '''
      }
    }

    stage('docker build') {
      steps {
        script {
          env.GIT_SHA_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
          env.IMAGE_TAG = params.DOCKER_TAG?.trim() ? params.DOCKER_TAG.trim() : "${BUILD_NUMBER}-${env.GIT_SHA_SHORT}"
          env.FULL_IMAGE = "${params.DOCKER_REGISTRY}/${params.DOCKER_IMAGE}:${env.IMAGE_TAG}"
          sh 'docker build -t "${FULL_IMAGE}" .'
        }
      }
    }

    stage('publish docker image') {
      steps {
        script {
          if (params.PUBLISH_DOCKER_IMAGE) {
            withCredentials([usernamePassword(credentialsId: 'docker-registry-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
              sh '''#!/usr/bin/env bash
                set -euo pipefail
                echo "${DOCKER_PASS}" | docker login "${DOCKER_REGISTRY}" -u "${DOCKER_USER}" --password-stdin
                docker push "${FULL_IMAGE}"
                docker logout "${DOCKER_REGISTRY}" || true
              '''
            }
          } else {
            echo 'Skipping Docker image publish (PUBLISH_DOCKER_IMAGE=false)'
          }
        }
      }
    }

    stage('declarative post actions') {
      steps {
        echo 'Declarative post actions are configured in the post block.'
      }
    }
  }

  post {
    success {
      echo "Pipeline completed successfully. Image: ${env.FULL_IMAGE ?: 'not built'}"
    }
    unsuccessful {
      echo 'Pipeline finished with failures.'
    }
    always {
      cleanWs()
    }
  }
}
