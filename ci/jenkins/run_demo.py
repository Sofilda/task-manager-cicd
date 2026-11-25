"""Запускает контрольные сценарии варианта 15 в Jenkins и снимает скриншоты интерфейса.

Результат: каталог evidence/ — журналы сборок (logs/), сводка (summary.json)
и скриншоты страниц Jenkins (screenshots/).
"""
import json
import os
import time

import requests
from playwright.sync_api import sync_playwright

J = 'http://localhost:8080'
JOB = 'Task-Manager-Variant15'
OUT = 'evidence'
os.makedirs(f'{OUT}/logs', exist_ok=True)
os.makedirs(f'{OUT}/screenshots', exist_ok=True)

SCENARIOS = [
    {'SIMULATE_RESULT': 'NONE'},
    {'SIMULATE_RESULT': 'FAILURE'},
    {'SIMULATE_RESULT': 'UNSTABLE'},
    {'SIMULATE_RESULT': 'ABORTED'},
    {'SIMULATE_RESULT': 'NONE', 'MIN_LINE_COVERAGE': '0.99'},
]


def trigger(params):
    r = requests.post(f'{J}/job/{JOB}/buildWithParameters', params=params, timeout=30)
    r.raise_for_status()
    queue_url = r.headers['Location'].rstrip('/') + '/api/json'
    for _ in range(600):
        q = requests.get(queue_url, timeout=30).json()
        if q.get('executable'):
            return q['executable']['number']
        time.sleep(2)
    raise RuntimeError('build did not leave the queue')


def wait_build(n):
    for _ in range(900):
        b = requests.get(f'{J}/job/{JOB}/{n}/api/json', timeout=30).json()
        if not b['building']:
            return b
        time.sleep(3)
    raise RuntimeError(f'build {n} did not finish')


summary = []
for params in SCENARIOS:
    n = trigger(params)
    print(f'Build #{n} started with {params}', flush=True)
    b = wait_build(n)
    log = requests.get(f'{J}/job/{JOB}/{n}/consoleText', timeout=60).text
    with open(f'{OUT}/logs/build-{n}.txt', 'w', encoding='utf-8') as f:
        f.write(log)
    tests = None
    try:
        t = requests.get(f'{J}/job/{JOB}/{n}/testReport/api/json?tree=failCount,passCount,skipCount', timeout=30)
        if t.ok:
            tests = t.json()
    except Exception:
        pass
    item = {'number': n, 'params': params, 'result': b['result'], 'duration_ms': b['duration'],
            'description': b.get('description'), 'tests': tests,
            'timestamp': b['timestamp'],
            'artifacts': [a['relativePath'] for a in b.get('artifacts', [])]}
    summary.append(item)
    print(json.dumps(item, ensure_ascii=False), flush=True)

with open(f'{OUT}/summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

# ------------------------------------------------------------------ скриншоты
FIND_JS = """(needle) => {
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n, last = null;
  while ((n = w.nextNode())) { if (n.textContent.includes(needle)) { last = n; } }
  if (!last) return false;
  last.parentElement.scrollIntoView({block: 'center'});
  return true;
}"""

FIND_FIRST_JS = FIND_JS.replace('{ last = n; }', '{ last = n; break; }')


def shot(page, name, url=None, needle=None, first=False, wait=1500, full=False):
    if url:
        page.goto(J + url, wait_until='networkidle')
    page.wait_for_timeout(wait)
    if needle:
        ok = page.evaluate(FIND_FIRST_JS if first else FIND_JS, needle)
        print(f'{name}: needle {needle!r} found={ok}', flush=True)
        page.wait_for_timeout(500)
    page.screenshot(path=f'{OUT}/screenshots/{name}.png', full_page=full)


nums = [s['number'] for s in summary]
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1366, 'height': 768}, locale='ru-RU')
    job = f'/job/{JOB}'

    shot(page, '01_job_page', job + '/', wait=4000)
    shot(page, '02_build_with_parameters', job + '/build?delay=0sec')
    # Сборка 1: SUCCESS
    shot(page, '03_build1_tests_run', f'{job}/{nums[0]}/console', needle='Tests run:', first=False)
    shot(page, '04_build1_notification', f'{job}/{nums[0]}/console', needle='УВЕДОМЛЕНИЕ CI')
    shot(page, '05_build1_page', f'{job}/{nums[0]}/')
    shot(page, '06_build1_test_report', f'{job}/{nums[0]}/testReport/')
    shot(page, '07_jacoco_report', f'{job}/{nums[0]}/artifact/target/site/jacoco/index.html')
    # Сборка 2: FAILURE
    shot(page, '08_build2_failure', f'{job}/{nums[1]}/console', needle='УВЕДОМЛЕНИЕ CI')
    shot(page, '09_build2_test_error', f'{job}/{nums[1]}/console', needle='Tests run:', first=True)
    # Сборка 3: UNSTABLE
    shot(page, '10_build3_unstable', f'{job}/{nums[2]}/console', needle='УВЕДОМЛЕНИЕ CI')
    shot(page, '11_build3_test_report', f'{job}/{nums[2]}/testReport/')
    # Сборка 4: ABORTED
    shot(page, '12_build4_aborted', f'{job}/{nums[3]}/console', needle='УВЕДОМЛЕНИЕ CI')
    # Сборка 5: quality gate
    shot(page, '13_build5_rule_violated', f'{job}/{nums[4]}/console', needle='Rule violated')
    shot(page, '14_build5_notification', f'{job}/{nums[4]}/console', needle='УВЕДОМЛЕНИЕ CI')
    # Итоговая страница задания с историей
    shot(page, '15_job_page_final', job + '/', wait=4000)
    browser.close()

print('done', flush=True)
