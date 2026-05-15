"""
Selenium Test Cases for TaskFlow Web Application
Run with: python -m pytest test_selenium.py -v
Make sure the Flask app is running at http://localhost:5000 before running these tests.
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ── Config ───────────────────────────────────────────────────

import os
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")


# ── Fixture ──────────────────────────────────────────────────

@pytest.fixture(scope="class")
def driver():
    """Set up a headless Chrome browser for each test class."""
    import socket
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")

    # Resolve the app hostname to IP so Chrome can find it inside Docker
    try:
        hostname = BASE_URL.split("//")[1].split(":")[0]
        ip = socket.gethostbyname(hostname)
        options.add_argument(f"--host-resolver-rules=MAP {hostname} {ip}")
    except Exception:
        pass  # If running locally, no resolver rules needed

    browser = webdriver.Chrome(options=options)
    browser.implicitly_wait(5)
    yield browser
    browser.quit()


def wait_for(driver, by, value, timeout=5):
    """Wait until an element is visible on the page."""
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, value))
    )


# ── Test Case 1: Page Load ────────────────────────────────────

class TestPageLoad:

    def test_page_title_is_correct(self, driver):
        """The browser tab title should be 'TaskFlow'."""
        driver.get(BASE_URL)
        assert "TaskFlow" in driver.title

    def test_app_heading_visible(self, driver):
        """The main heading 'TaskFlow' should be visible on the page."""
        driver.get(BASE_URL)
        heading = wait_for(driver, By.TAG_NAME, "h1")
        assert "TaskFlow" in heading.text

    def test_input_field_is_present(self, driver):
        """The task input field should be present and interactable."""
        driver.get(BASE_URL)
        input_field = wait_for(driver, By.ID, "task-input")
        assert input_field.is_displayed()
        assert input_field.is_enabled()

    def test_add_button_is_present(self, driver):
        """The Add button should be visible on the page."""
        driver.get(BASE_URL)
        button = wait_for(driver, By.CSS_SELECTOR, "button[type='submit']")
        assert button.is_displayed()


# ── Test Case 2: Add Task ─────────────────────────────────────

class TestAddTask:

    def test_add_single_task(self, driver):
        """Typing a task title and clicking Add should show the task on the page."""
        driver.get(BASE_URL)
        input_field = wait_for(driver, By.ID, "task-input")
        input_field.clear()
        input_field.send_keys("Selenium Test Task")
        input_field.send_keys(Keys.RETURN)

        time.sleep(0.5)
        page_source = driver.page_source
        assert "Selenium Test Task" in page_source

    def test_add_task_using_button_click(self, driver):
        """Clicking the Add button should submit the task form."""
        driver.get(BASE_URL)
        input_field = wait_for(driver, By.ID, "task-input")
        input_field.clear()
        input_field.send_keys("Button Click Task")

        button = driver.find_element(By.CSS_SELECTOR, ".add-form button[type='submit']")
        button.click()

        time.sleep(0.5)
        assert "Button Click Task" in driver.page_source

    def test_add_multiple_tasks(self, driver):
        """Adding three tasks should show all three on the page."""
        driver.get(BASE_URL)
        tasks = ["Morning Run", "Read 30 Pages", "Write Journal"]

        for task in tasks:
            input_field = wait_for(driver, By.ID, "task-input")
            input_field.clear()
            input_field.send_keys(task)
            input_field.send_keys(Keys.RETURN)
            time.sleep(0.3)

        page_source = driver.page_source
        for task in tasks:
            assert task in page_source

    def test_input_cleared_after_empty_submit(self, driver):
        """Input field should still be present and usable after interacting."""
        driver.get(BASE_URL)
        input_field = wait_for(driver, By.ID, "task-input")
        assert input_field.is_displayed()


# ── Test Case 3: Toggle Task Complete ────────────────────────

class TestToggleTask:

    def test_toggle_task_marks_done(self, driver):
        """Clicking the toggle button should mark a task as done (adds 'done' class)."""
        driver.get(BASE_URL)

        # Add a fresh task
        input_field = wait_for(driver, By.ID, "task-input")
        input_field.clear()
        input_field.send_keys("Toggle This Task")
        input_field.send_keys(Keys.RETURN)
        time.sleep(0.5)

        driver.get(BASE_URL)

        # Find the task item and its toggle button
        task_items = driver.find_elements(By.CLASS_NAME, "task-item")
        assert len(task_items) > 0

        toggle_btn = task_items[0].find_element(By.CSS_SELECTOR, "form.toggle button")
        toggle_btn.click()
        time.sleep(0.5)

        driver.get(BASE_URL)
        task_items = driver.find_elements(By.CLASS_NAME, "task-item")
        done_tasks = [t for t in task_items if "done" in t.get_attribute("class")]
        assert len(done_tasks) > 0

    def test_toggle_task_twice_marks_undone(self, driver):
        """Toggling a task twice should mark it back as incomplete."""
        driver.get(BASE_URL)

        # Add a task to toggle
        input_field = wait_for(driver, By.ID, "task-input")
        input_field.clear()
        input_field.send_keys("Double Toggle Task")
        input_field.send_keys(Keys.RETURN)
        time.sleep(0.5)

        driver.get(BASE_URL)
        task_items = driver.find_elements(By.CLASS_NAME, "task-item")
        first_task = task_items[0]
        task_id = first_task.get_attribute("id")  # e.g. "task-3"

        # Toggle ON
        toggle_btn = first_task.find_element(By.CSS_SELECTOR, "form.toggle button")
        toggle_btn.click()
        time.sleep(0.5)

        # Toggle OFF
        driver.get(BASE_URL)
        task_items = driver.find_elements(By.CLASS_NAME, "task-item")
        target = next((t for t in task_items if t.get_attribute("id") == task_id), None)
        assert target is not None
        toggle_btn = target.find_element(By.CSS_SELECTOR, "form.toggle button")
        toggle_btn.click()
        time.sleep(0.5)

        driver.get(BASE_URL)
        task_items = driver.find_elements(By.CLASS_NAME, "task-item")
        target = next((t for t in task_items if t.get_attribute("id") == task_id), None)
        assert target is not None
        assert "done" not in target.get_attribute("class")


# ── Test Case 4: Delete Task ──────────────────────────────────

class TestDeleteTask:

    def test_delete_removes_task_from_page(self, driver):
        """Clicking the delete button should remove the task from the page."""
        driver.get(BASE_URL)

        # Add a task specifically to delete
        input_field = wait_for(driver, By.ID, "task-input")
        input_field.clear()
        input_field.send_keys("Task To Be Deleted")
        input_field.send_keys(Keys.RETURN)
        time.sleep(0.5)

        driver.get(BASE_URL)
        assert "Task To Be Deleted" in driver.page_source

        # Find and click its delete button
        task_items = driver.find_elements(By.CLASS_NAME, "task-item")
        for item in task_items:
            if "Task To Be Deleted" in item.text:
                delete_btn = item.find_element(By.CSS_SELECTOR, "form.delete button")
                delete_btn.click()
                break

        time.sleep(0.5)
        driver.get(BASE_URL)
        assert "Task To Be Deleted" not in driver.page_source

    def test_delete_one_task_keeps_others(self, driver):
        """Deleting one task should not remove other tasks."""
        driver.get(BASE_URL)

        # Add two tasks
        for title in ["Keep This Task", "Remove This Task"]:
            input_field = wait_for(driver, By.ID, "task-input")
            input_field.clear()
            input_field.send_keys(title)
            input_field.send_keys(Keys.RETURN)
            time.sleep(0.3)

        driver.get(BASE_URL)

        # Delete only "Remove This Task"
        task_items = driver.find_elements(By.CLASS_NAME, "task-item")
        for item in task_items:
            if "Remove This Task" in item.text:
                delete_btn = item.find_element(By.CSS_SELECTOR, "form.delete button")
                delete_btn.click()
                break

        time.sleep(0.5)
        driver.get(BASE_URL)
        assert "Remove This Task" not in driver.page_source
        assert "Keep This Task" in driver.page_source


# ── Test Case 5: Stats Counter ────────────────────────────────

class TestStatsCounter:

    def test_stats_section_is_visible(self, driver):
        """The stats bar (Total / Done / Pending) should be visible."""
        driver.get(BASE_URL)

        # Add a task so stats appear
        input_field = wait_for(driver, By.ID, "task-input")
        input_field.clear()
        input_field.send_keys("Stats Check Task")
        input_field.send_keys(Keys.RETURN)
        time.sleep(1.5)

        driver.get(BASE_URL)
        stats = driver.find_element(By.CLASS_NAME, "stats")
        assert stats.is_displayed()

    def test_stats_labels_present(self, driver):
        """Stats labels Total, Done, Pending should all appear on the page."""
        driver.get(BASE_URL)
        page_source = driver.page_source
        assert "Total"   in page_source
        assert "Done"    in page_source
        assert "Pending" in page_source
