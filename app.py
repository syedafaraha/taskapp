from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ── Database Model ──────────────────────────────────────────
class Task(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    title     = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed,
            'created_at': self.created_at.strftime('%b %d, %Y')
        }

# ── Routes ──────────────────────────────────────────────────
@app.route('/')
def index():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    title = request.form.get('title', '').strip()
    if title:
        task = Task(title=title)
        db.session.add(task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/toggle/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = not task.completed
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

# ── API endpoints (used by Selenium/unit tests) ─────────────
@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks])

@app.route('/api/tasks', methods=['POST'])
def api_add_task():
    data = request.get_json()
    if not data or not data.get('title', '').strip():
        return jsonify({'error': 'Title is required'}), 400
    task = Task(title=data['title'].strip())
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201

# ── Init ────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
