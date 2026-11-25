# task-manager-cicd — ЛР №4 (ИППРПО), вариант 15

Федоренко Софья Алексеевна, группа 472302.

Учебное REST-приложение (Spring Boot, Java 21) и два CI-конвейера:

* `Jenkinsfile` — Jenkins Declarative Pipeline. Вариант 15, часть 1: уведомления о результате
  (SUCCESS / FAILURE / UNSTABLE / ABORTED). Параметр `SIMULATE_RESULT` воспроизводит каждое состояние.
* `.github/workflows/ci.yml` — GitHub Actions. Вариант 15, часть 2: контроль покрытия кода
  (JaCoCo quality gate, пороги задаются при ручном запуске).
* `.github/workflows/jenkins-demo.yml` — учебный стенд: Jenkins LTS в Docker на runner-е,
  прогон контрольных сценариев, журналы и скриншоты — в ветке `ci-evidence`.

Локальная проверка:

    mvn -B -ntp clean verify
    mvn -B -ntp clean verify -Dcoverage.line.minimum=0.99   # quality gate не пройден
