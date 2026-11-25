package by.edu.example.taskmanager;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;

import static org.junit.jupiter.api.Assertions.fail;

/**
 * Учебный тест для демонстрации состояний FAILURE и UNSTABLE в CI (вариант 15).
 * В обычной сборке он ВЫКЛЮЧЕН и не учитывается в отчёте.
 * Включается только явным параметром Maven: -Dci.demo.failTest=true
 */
class CiDemoTest {

    @Test
    @EnabledIfSystemProperty(named = "ci.demo.failTest", matches = "true")
    void controlledFailureForCiDemo() {
        fail("Контролируемая ошибка: демонстрация обработки неуспешного результата в CI");
    }
}
