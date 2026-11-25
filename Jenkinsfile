/*
 * Jenkinsfile — лабораторная работа №4, вариант 15.
 * Основа: базовый конвейер из методического пособия (часть 1).
 *
 * Индивидуальное задание, часть 1 (Jenkins, вариант 15):
 *   уведомление о результате выполнения Pipeline с отдельной
 *   обработкой и сообщениями для SUCCESS, FAILURE, UNSTABLE, ABORTED.
 *
 * Индивидуальное задание, часть 2 (вариант 15) — контроль покрытия кода
 * тестами — сначала отлажено здесь (параметры MIN_*_COVERAGE + JaCoCo check),
 * затем перенесено в GitHub Actions (.github/workflows/ci.yml).
 */

// ---------------------------------------------------------------------------
// Уведомление о результате сборки (вариант 15).
// Канал уведомления:
//   1) Console Output — оформленный блок сообщения;
//   2) описание сборки (видно в истории сборок на странице задания);
//   3) файл notifications/build-notification.txt в артефактах сборки;
//   4) e-mail — необязательно, если задан NOTIFY_EMAIL и настроен SMTP.
// ---------------------------------------------------------------------------
def notifyBuild(String status) {
    def meta = [
        SUCCESS : [icon: '✅', title: 'Сборка успешна',
                   advice: 'Все проверки пройдены, порог покрытия выполнен, JAR сохранён в артефактах.'],
        FAILURE : [icon: '❌', title: 'Сборка завершилась ошибкой',
                   advice: 'Откройте Console Output и найдите первую ошибку (компиляция, тесты, quality gate JaCoCo).'],
        UNSTABLE: [icon: '⚠️', title: 'Сборка нестабильна',
                   advice: 'Сборка выполнена, но есть упавшие тесты. Проверьте раздел Test Result.'],
        ABORTED : [icon: '⏹', title: 'Сборка прервана',
                   advice: 'Выполнение остановлено вручную или по тайм-ауту. Результаты неполные — перезапустите сборку.']
    ]
    def m = meta[status] ?: [icon: '❔', title: "Статус ${status}", advice: 'Неизвестный статус.']

    def tests = env.TESTS_TOTAL ?
        "всего ${env.TESTS_TOTAL}, упало ${env.TESTS_FAILED}, пропущено ${env.TESTS_SKIPPED}" :
        'результаты тестов не сформированы'
    def coverage = env.COVERAGE_SUMMARY ?: 'отчёт JaCoCo не сформирован'

    def message = """\
${m.icon} [${status}] ${m.title}
Задание     : ${env.JOB_NAME} #${env.BUILD_NUMBER}
Ветка/commit: ${env.GIT_BRANCH ?: '-'} / ${env.GIT_COMMIT ? env.GIT_COMMIT.substring(0, 7) : '-'}
Режим       : SIMULATE_RESULT=${params.SIMULATE_RESULT}
Тесты       : ${tests}
Покрытие    : ${coverage} (порог LINE ${params.MIN_LINE_COVERAGE}, BRANCH ${params.MIN_BRANCH_COVERAGE})
Длительность: ${currentBuild.durationString.replace(' and counting', '')}
Что делать  : ${m.advice}
Ссылка      : ${env.BUILD_URL}
"""

    echo "==================== УВЕДОМЛЕНИЕ CI ====================\n${message}========================================================"

    currentBuild.description = "${m.icon} ${status}: ${m.title}"

    writeFile file: 'notifications/build-notification.txt', text: message, encoding: 'UTF-8'
    archiveArtifacts artifacts: 'notifications/build-notification.txt', allowEmptyArchive: true

    if (params.NOTIFY_EMAIL?.trim()) {
        try {
            mail to: params.NOTIFY_EMAIL.trim(),
                 subject: "${m.icon} [${status}] ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                 body: message
            echo "Уведомление отправлено на ${params.NOTIFY_EMAIL}"
        } catch (err) {
            // Отсутствие SMTP не должно менять результат сборки.
            echo "E-mail не отправлен (SMTP не настроен?): ${err.message}"
        }
    }
}

// Запуск команды оболочки: bat на Windows-агенте, sh на Linux-агенте.
def runCmd(String command) {
    if (isUnix()) {
        sh command
    } else {
        bat command
    }
}

pipeline {
    /*
     * На учебном стенде из методички: agent { label 'windows-java21-agent' }.
     * Здесь — любой узел с Java 21, Maven и Git (Windows или Linux).
     */
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        choice(name: 'SIMULATE_RESULT',
               choices: ['NONE', 'FAILURE', 'UNSTABLE', 'ABORTED'],
               description: 'Вариант 15: контролируемый сценарий для проверки уведомлений. NONE — обычная сборка.')
        string(name: 'MIN_LINE_COVERAGE', defaultValue: '0.80',
               description: 'Минимальная доля покрытых строк (JaCoCo LINE COVEREDRATIO)')
        string(name: 'MIN_BRANCH_COVERAGE', defaultValue: '0.60',
               description: 'Минимальная доля покрытых ветвлений (JaCoCo BRANCH COVEREDRATIO)')
        string(name: 'NOTIFY_EMAIL', defaultValue: '',
               description: 'Необязательно: адрес для e-mail уведомления (нужен настроенный SMTP)')
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Получение исходного кода из Git'
                script {
                    def scmVars = checkout scm
                    env.GIT_COMMIT = scmVars.GIT_COMMIT
                    env.GIT_BRANCH = scmVars.GIT_BRANCH
                }
            }
        }

        stage('Toolchain') {
            steps {
                runCmd 'java -version'
                runCmd 'mvn -version'
                runCmd 'git --version'
            }
        }

        stage('Build and Verify') {
            steps {
                script {
                    def cmd = "mvn -B -ntp clean verify" +
                              " -Dcoverage.line.minimum=${params.MIN_LINE_COVERAGE}" +
                              " -Dcoverage.branch.minimum=${params.MIN_BRANCH_COVERAGE}"
                    if (params.SIMULATE_RESULT == 'FAILURE') {
                        // Учебный тест CiDemoTest включается и падает -> Maven BUILD FAILURE
                        cmd += ' -Dci.demo.failTest=true'
                    } else if (params.SIMULATE_RESULT == 'UNSTABLE') {
                        // Тест падает, но Maven не прерывает сборку;
                        // шаг junit увидит падение и пометит сборку как UNSTABLE
                        cmd += ' -Dci.demo.failTest=true -Dmaven.test.failure.ignore=true'
                    }
                    echo "Команда Maven: ${cmd}"
                    runCmd cmd
                }
            }
            post {
                always {
                    script {
                        def r = junit(allowEmptyResults: true,
                                      testResults: 'target/surefire-reports/TEST-*.xml,target/failsafe-reports/TEST-*.xml')
                        env.TESTS_TOTAL   = "${r.totalCount}"
                        env.TESTS_FAILED  = "${r.failCount}"
                        env.TESTS_SKIPPED = "${r.skipCount}"
                    }
                    archiveArtifacts artifacts: 'target/surefire-reports/**,target/failsafe-reports/**,target/site/**',
                                     allowEmptyArchive: true
                }
            }
        }

        // Часть 2 (вариант 15), локальная отладка: сводка покрытия из jacoco.csv.
        // Сам quality gate выполняется в Maven (jacoco:check на фазе verify).
        stage('Coverage Summary') {
            steps {
                script {
                    if (isUnix()) {
                        // jacoco.csv: 6-7 — BRANCH missed/covered, 8-9 — LINE missed/covered
                        sh '''
                            csv=target/site/jacoco/jacoco.csv
                            test -f "$csv" || { echo "jacoco.csv не найден"; exit 1; }
                            awk -F, 'NR>1 {bm+=$6; bc+=$7; lm+=$8; lc+=$9}
                                END {printf "LINE %.1f%% (%d/%d), BRANCH %.1f%% (%d/%d)\\n",
                                     100*lc/(lc+lm), lc, lc+lm, 100*bc/(bc+bm), bc, bc+bm}' "$csv" \\
                                > target/coverage-summary.txt
                            cat target/coverage-summary.txt
                        '''
                    } else {
                        powershell '''
                            $csv = 'target/site/jacoco/jacoco.csv'
                            if (-not (Test-Path $csv)) { Write-Host 'jacoco.csv не найден'; exit 1 }
                            $rows = Import-Csv $csv
                            $lc = ($rows | Measure-Object LINE_COVERED   -Sum).Sum
                            $lm = ($rows | Measure-Object LINE_MISSED    -Sum).Sum
                            $bc = ($rows | Measure-Object BRANCH_COVERED -Sum).Sum
                            $bm = ($rows | Measure-Object BRANCH_MISSED  -Sum).Sum
                            $line   = [math]::Round(100 * $lc / ($lc + $lm), 1)
                            $branch = [math]::Round(100 * $bc / ($bc + $bm), 1)
                            "LINE $line% ($lc/$($lc+$lm)), BRANCH $branch% ($bc/$($bc+$bm))" |
                                Out-File -Encoding ascii target/coverage-summary.txt
                            Get-Content target/coverage-summary.txt
                        '''
                    }
                }
                script {
                    env.COVERAGE_SUMMARY = readFile('target/coverage-summary.txt').trim()
                }
            }
        }

        // Вариант 15: имитация прерывания. timeout останавливает шаг,
        // Jenkins присваивает сборке статус ABORTED.
        stage('Simulate Abort') {
            when { expression { params.SIMULATE_RESULT == 'ABORTED' } }
            steps {
                timeout(time: 10, unit: 'SECONDS') {
                    echo 'Долгая операция — будет прервана тайм-аутом через 10 секунд'
                    runCmd(isUnix() ? 'sleep 60' : 'ping -n 60 127.0.0.1 > nul')
                }
            }
        }
    }

    post {
        success {
            archiveArtifacts artifacts: 'target/task-manager-cicd-1.0.0.jar', fingerprint: true
            notifyBuild('SUCCESS')
        }
        unstable {
            notifyBuild('UNSTABLE')
        }
        failure {
            notifyBuild('FAILURE')
        }
        aborted {
            notifyBuild('ABORTED')
        }
    }
}
