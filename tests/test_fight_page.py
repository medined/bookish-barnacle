from __future__ import annotations

import os
from pathlib import Path

import pytest
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

PAGE_URL = (Path(__file__).resolve().parent.parent / "fight.html").resolve().as_uri()


@pytest.fixture(scope="module")
def driver() -> WebDriver:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(log_output=os.devnull)
    browser = Chrome(options=options, service=service)
    yield browser
    browser.quit()


def wait_for_options(driver: WebDriver, select_id: str, minimum: int = 2) -> Select:
    wait = WebDriverWait(driver, 10)

    def _has_options(drv: WebDriver) -> bool:
        select = Select(drv.find_element(By.ID, select_id))
        return len(select.options) >= minimum

    wait.until(_has_options)
    return Select(driver.find_element(By.ID, select_id))


def test_dropdowns_populate_with_heroes(driver: WebDriver) -> None:
    driver.get(PAGE_URL)
    hero_a = wait_for_options(driver, "heroA", minimum=5)
    hero_b = wait_for_options(driver, "heroB", minimum=5)
    assert len(hero_a.options) == len(hero_b.options)
    assert len(hero_a.options) >= 5
    hero_names = [option.text.strip() for option in hero_a.options]
    assert "D.Va" in hero_names
    assert "Tracer" in hero_names


def test_fight_button_runs_simulation(driver: WebDriver) -> None:
    driver.get(PAGE_URL)
    hero_a = wait_for_options(driver, "heroA")
    hero_b = wait_for_options(driver, "heroB")
    hero_a.select_by_visible_text("D.Va")
    hero_b.select_by_visible_text("Tracer")

    fight_button = driver.find_element(By.CSS_SELECTOR, "form.controls button[type='submit']")
    fight_button.click()

    def _summary_has_names(drv: WebDriver):
        element = drv.find_element(By.ID, "summary")
        text = element.text
        return element if ("D.Va" in text and "Tracer" in text) else False

    summary = WebDriverWait(driver, 10).until(_summary_has_names)

    assert "D.Va" in summary.text and "Tracer" in summary.text
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#log article")))
    log_entries = driver.find_elements(By.CSS_SELECTOR, "#log article")
    assert log_entries
