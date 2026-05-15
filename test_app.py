import pytest
import json
from app import app, db, Task


# ── Fixtures ────────────────────────────────────────────────

@pytest.fixture
def client():
    """Set up a test client with a fresh in-memory database."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


# ── Helper ──────────────────────────────────────────────────

def add_task(client, title):
    """Helper: POST a task via the web form."""
    return client.post('/add', data={'title': title}, follow_redirects=True)


# ── Tests: Web Routes ────────────────────────────────────────

class TestHomePage:

    def test_home_page_loads(self, client):
        """Home page should return HTTP 200."""
        response = client.get('/')
        assert response.status_code == 200

    def test_home_page_contains_app_name(self, client):
        """Home page should contain the app name."""
        response = client.get('/')
        assert b'TaskFlow' in response.data

    def test_home_page_shows_empty_message_when_no_tasks(self, client):
        """Home page should show empty state when there are no tasks."""
        response = client.get('/')
        assert b'No tasks yet' in response.data


class TestAddTask:

    def test_add_task_redirects(self, client):
        """Adding a task should redirect back to home."""
        response = client.post('/add', data={'title': 'Buy groceries'})
        assert response.status_code == 302

    def test_add_task_appears_on_page(self, client):
        """Added task should appear on the home page."""
        add_task(client, 'Buy groceries')
        response = client.get('/')
        assert b'Buy groceries' in response.data

    def test_add_multiple_tasks(self, client):
        """Multiple tasks should all appear on the home page."""
        add_task(client, 'Task One')
        add_task(client, 'Task Two')
        add_task(client, 'Task Three')
        response = client.get('/')
        assert b'Task One'   in response.data
        assert b'Task Two'   in response.data
        assert b'Task Three' in response.data

    def test_add_empty_task_ignored(self, client):
        """Submitting a blank title should not create a task."""
        add_task(client, '   ')          # whitespace only
        response = client.get('/')
        assert b'No tasks yet' in response.data

    def test_add_task_saved_to_database(self, client):
        """Task should be persisted in the database."""
        add_task(client, 'Database check')
        with app.app_context():
            task = Task.query.filter_by(title='Database check').first()
            assert task is not None


class TestToggleTask:

    def test_toggle_marks_task_complete(self, client):
        """Toggling an incomplete task should mark it done."""
        add_task(client, 'Walk the dog')
        with app.app_context():
            task = Task.query.first()
            assert task.completed is False
            task_id = task.id

        client.post(f'/toggle/{task_id}', follow_redirects=True)

        with app.app_context():
            task = Task.query.get(task_id)
            assert task.completed is True

    def test_toggle_twice_returns_to_incomplete(self, client):
        """Toggling a task twice should leave it incomplete."""
        add_task(client, 'Read a book')
        with app.app_context():
            task_id = Task.query.first().id

        client.post(f'/toggle/{task_id}')
        client.post(f'/toggle/{task_id}')

        with app.app_context():
            task = Task.query.get(task_id)
            assert task.completed is False


class TestDeleteTask:

    def test_delete_task_removes_it(self, client):
        """Deleted task should no longer appear on the page."""
        add_task(client, 'Task to delete')
        with app.app_context():
            task_id = Task.query.first().id

        client.post(f'/delete/{task_id}', follow_redirects=True)
        response = client.get('/')
        assert b'Task to delete' not in response.data

    def test_delete_task_removed_from_database(self, client):
        """Deleted task should be removed from the database."""
        add_task(client, 'Delete from DB')
        with app.app_context():
            task_id = Task.query.first().id

        client.post(f'/delete/{task_id}')

        with app.app_context():
            task = Task.query.get(task_id)
            assert task is None

    def test_delete_nonexistent_task_returns_404(self, client):
        """Deleting a task that doesn't exist should return 404."""
        response = client.post('/delete/9999')
        assert response.status_code == 404


# ── Tests: REST API ──────────────────────────────────────────

class TestApiGetTasks:

    def test_api_returns_empty_list(self, client):
        """API should return an empty list when no tasks exist."""
        response = client.get('/api/tasks')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []

    def test_api_returns_added_tasks(self, client):
        """API should return tasks that were added."""
        add_task(client, 'API Task 1')
        add_task(client, 'API Task 2')
        response = client.get('/api/tasks')
        data = json.loads(response.data)
        assert len(data) == 2

    def test_api_task_has_required_fields(self, client):
        """Each task in API response should have id, title, completed, created_at."""
        add_task(client, 'Field check')
        response = client.get('/api/tasks')
        task = json.loads(response.data)[0]
        assert 'id'         in task
        assert 'title'      in task
        assert 'completed'  in task
        assert 'created_at' in task


class TestApiAddTask:

    def test_api_add_task_returns_201(self, client):
        """POST /api/tasks should return 201 Created."""
        response = client.post(
            '/api/tasks',
            data=json.dumps({'title': 'New via API'}),
            content_type='application/json'
        )
        assert response.status_code == 201

    def test_api_add_task_returns_task_data(self, client):
        """POST /api/tasks should return the created task."""
        response = client.post(
            '/api/tasks',
            data=json.dumps({'title': 'Return check'}),
            content_type='application/json'
        )
        task = json.loads(response.data)
        assert task['title'] == 'Return check'
        assert task['completed'] is False

    def test_api_add_task_without_title_returns_400(self, client):
        """POST /api/tasks with no title should return 400."""
        response = client.post(
            '/api/tasks',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_api_add_task_empty_title_returns_400(self, client):
        """POST /api/tasks with empty title should return 400."""
        response = client.post(
            '/api/tasks',
            data=json.dumps({'title': '   '}),
            content_type='application/json'
        )
        assert response.status_code == 400


# ── Tests: Database Model ────────────────────────────────────

class TestTaskModel:

    def test_task_default_completed_is_false(self, client):
        """New task should have completed=False by default."""
        with app.app_context():
            task = Task(title='Default check')
            db.session.add(task)
            db.session.commit()
            assert task.completed is False

    def test_task_to_dict(self, client):
        """Task.to_dict() should return a valid dictionary."""
        with app.app_context():
            task = Task(title='Dict check')
            db.session.add(task)
            db.session.commit()
            d = task.to_dict()
            assert d['title'] == 'Dict check'
            assert d['completed'] is False
            assert 'id' in d and 'created_at' in d
