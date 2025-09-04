from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import joinedload
import pandas as pd
import os
from datetime import datetime, timedelta
from evaluator_selector import get_evaluator_from_config
from evaluator_config import get_evaluator_config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exam_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize evaluator as main evaluation engine
try:
    config = get_evaluator_config()
    evaluator_type = config.get('default_evaluator_type', 'ai')
    ai_evaluator = get_evaluator_from_config(evaluator_type)
    
    print(f"✅ {evaluator_type.upper()}Evaluator initialized successfully")
    
    # Handle different evaluator types
    if hasattr(ai_evaluator, 'config') and hasattr(ai_evaluator.config, 'bi_encoder_name'):
        # AIEvaluator
        print(f"📊 Models: Bi-encoder ({ai_evaluator.config.bi_encoder_name}), Cross-encoder (L12-v2)")
        print(f"⚙️  Config: Cache directory={ai_evaluator.config.cache_dir}")
    elif hasattr(ai_evaluator, 'model') and ai_evaluator.model:
        # OptimizedSASEvaluator
        print(f"📊 Model loaded: {ai_evaluator.model_name}")
        print(f"⚙️  Config: Threshold={ai_evaluator.threshold}, Max marks={ai_evaluator.max_marks}")
        print(f"🎯 Device: {ai_evaluator.device}, Batch size: {ai_evaluator.batch_size}")
    elif hasattr(ai_evaluator, 'models') and ai_evaluator.models:
        # ModelBasedCriticalWordEvaluator (if available)
        print(f"📊 Models loaded: {list(ai_evaluator.models.keys())}")
        print(f"⚙️  Config: Cache directory={ai_evaluator.cache_dir}")
        print(f"🎯 Thresholds: Pass={ai_evaluator.pass_threshold}, Max={ai_evaluator.max_marks}")
    else:
        # CleanEvaluator (fallback)
        print(f"📊 Models loaded: {list(ai_evaluator.models.keys())}")
        print(f"⚙️  Config: Cache directory={ai_evaluator.config.cache_dir}")
        
except Exception as e:
    print(f"❌ Failed to initialize evaluator: {e}")
    print("Please ensure the required models are in the adaptive_cache directory:")
    print("- sentence-transformers_all-mpnet-base-v2/")
    print("- sentence-transformers_all-MiniLM-L12-v2/")
    print("- Additional models for ModelBasedCriticalWordEvaluator")
    ai_evaluator = None

# Database Models
class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    students = db.relationship('User', backref='department', lazy=True)
    exams = db.relationship('Exam', backref='department', lazy=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'student'
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)  # Only for students
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)  # Exam duration in minutes
    start_time = db.Column(db.DateTime, nullable=True)  # When exam starts
    end_time = db.Column(db.DateTime, nullable=True)  # When exam ends
    is_enabled = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=False)  # Whether exam is currently running
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.relationship('Question', backref='exam', lazy=True, cascade='all, delete-orphan')
    results = db.relationship('Result', backref='exam', lazy=True, cascade='all, delete-orphan')

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    reference_answer = db.Column(db.Text, nullable=False)
    max_marks = db.Column(db.Integer, nullable=False)
    question_order = db.Column(db.Integer, default=0)

class ExamSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    time_remaining = db.Column(db.Integer, nullable=True)  # Minutes remaining
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    exam = db.relationship('Exam', backref='sessions')
    student = db.relationship('User', backref='exam_sessions')

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('exam_session.id'), nullable=True)
    student_answer = db.Column(db.Text)
    ai_score = db.Column(db.Float)
    marks_awarded = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('User', backref='results')
    question = db.relationship('Question', backref='results')
    session = db.relationship('ExamSession', backref='results')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

# Admin Routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('student_dashboard'))
    
    exams = Exam.query.order_by(Exam.created_at.desc()).all()
    return render_template('admin_dashboard.html', exams=exams)

@app.route('/admin/departments')
@login_required
def manage_departments():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('student_dashboard'))
    
    departments = Department.query.all()
    return render_template('manage_departments.html', departments=departments)

@app.route('/admin/create_department', methods=['POST'])
@login_required
def create_department():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    if not name:
        return jsonify({'error': 'Department name is required'}), 400
    
    # Check if department already exists
    existing = Department.query.filter_by(name=name).first()
    if existing:
        return jsonify({'error': 'Department already exists'}), 400
    
    department = Department(name=name, description=description)
    db.session.add(department)
    db.session.commit()
    
    return jsonify({'message': 'Department created successfully!'})

@app.route('/admin/department/<int:department_id>')
@login_required
def department_details(department_id):
    """Show detailed view of a department including its exams and students."""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('student_dashboard'))
    
    department = Department.query.get_or_404(department_id)
    
    # Get all exams for this department with their statistics
    exams = Exam.query.filter_by(department_id=department_id).all()
    
    # Get exam statistics
    exam_stats = []
    for exam in exams:
        # Count students who took this exam
        students_taken = db.session.query(Result.student_id).filter_by(exam_id=exam.id).distinct().count()
        
        # Get average score
        avg_score = db.session.query(db.func.avg(Result.marks_awarded)).filter_by(exam_id=exam.id).scalar() or 0
        
        # Count total questions
        total_questions = len(exam.questions)
        
        exam_stats.append({
            'exam': exam,
            'students_taken': students_taken,
            'average_score': round(avg_score, 2),
            'total_questions': total_questions,
            'max_possible_score': sum(q.max_marks for q in exam.questions)
        })
    
    # Get students in this department
    students = User.query.filter_by(department_id=department_id, role='student').all()
    
    # Get student statistics
    student_stats = []
    for student in students:
        # Count exams taken by this student
        exams_taken = db.session.query(Result.exam_id).filter_by(student_id=student.id).distinct().count()
        
        # Get average score across all exams
        avg_score = db.session.query(db.func.avg(Result.marks_awarded)).filter_by(student_id=student.id).scalar() or 0
        
        student_stats.append({
            'student': student,
            'exams_taken': exams_taken,
            'average_score': round(avg_score, 2)
        })
    
    return render_template('department_details.html', 
                         department=department,
                         exam_stats=exam_stats,
                         student_stats=student_stats)

@app.route('/admin/create_exam', methods=['GET', 'POST'])
@login_required
def create_exam():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        department_id = int(request.form['department_id'])
        duration_minutes = int(request.form.get('duration_minutes', 60))
        
        exam = Exam(
            title=title, 
            description=description,
            department_id=department_id,
            duration_minutes=duration_minutes,
            is_active=True  # Set exam as active by default
        )
        db.session.add(exam)
        db.session.commit()
        
        flash('Exam created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    departments = Department.query.all()
    return render_template('create_exam.html', departments=departments)

@app.route('/admin/upload_csv/<int:exam_id>', methods=['POST'])
@login_required
def upload_csv(exam_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    exam = Exam.query.get_or_404(exam_id)
    
    if 'csv_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['csv_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read CSV file
        df = pd.read_csv(file)
        required_columns = ['question', 'answer', 'max_marks']
        
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'CSV must have columns: question, answer, max_marks'}), 400
        
        # Clear existing questions
        Question.query.filter_by(exam_id=exam_id).delete()
        
        # Add new questions
        for index, row in df.iterrows():
            question = Question(
                exam_id=exam_id,
                question_text=row['question'],
                reference_answer=row['answer'],
                max_marks=int(row['max_marks']),
                question_order=index + 1
            )
            db.session.add(question)
        
        db.session.commit()
        return jsonify({'message': 'Question bank uploaded successfully!'})
    
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/admin/toggle_exam/<int:exam_id>')
@login_required
def toggle_exam(exam_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    exam = Exam.query.get_or_404(exam_id)
    exam.is_enabled = not exam.is_enabled
    db.session.commit()
    
    status = 'enabled' if exam.is_enabled else 'disabled'
    flash(f'Exam {status} successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/start_exam/<int:exam_id>')
@login_required
def start_exam(exam_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    exam = Exam.query.get_or_404(exam_id)
    
    if exam.is_active:
        flash('Exam is already active!', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Start the exam
    exam.is_active = True
    exam.start_time = datetime.utcnow()
    exam.end_time = datetime.utcnow() + timedelta(minutes=exam.duration_minutes)
    db.session.commit()
    
    flash(f'Exam "{exam.title}" started successfully! Duration: {exam.duration_minutes} minutes', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/stop_exam/<int:exam_id>')
@login_required
def stop_exam(exam_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    exam = Exam.query.get_or_404(exam_id)
    
    if not exam.is_active:
        flash('Exam is not currently active!', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Stop the exam
    exam.is_active = False
    exam.end_time = datetime.utcnow()
    
    # Mark all active sessions as completed
    active_sessions = ExamSession.query.filter_by(exam_id=exam_id, is_completed=False).all()
    for session in active_sessions:
        session.is_completed = True
        session.end_time = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Exam "{exam.title}" stopped successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/exam_results/<int:exam_id>')
@login_required
def admin_exam_results(exam_id):
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('admin_dashboard'))
    
    exam = Exam.query.get_or_404(exam_id)
    
    # Get all students who took this exam with their results
    student_results = db.session.query(
        User.username,
        User.id.label('student_id'),
        db.func.count(Result.id).label('questions_answered'),
        db.func.sum(Result.marks_awarded).label('total_score'),
        db.func.avg(Result.ai_score).label('average_ai_score'),
        db.func.max(Result.submitted_at).label('submitted_at')
    ).join(Result, User.id == Result.student_id)\
     .filter(Result.exam_id == exam_id)\
     .group_by(User.id, User.username)\
     .order_by(db.func.sum(Result.marks_awarded).desc()).all()
    
    # Calculate exam statistics
    total_students = len(student_results)
    total_questions = len(exam.questions)
    max_possible_score = sum(q.max_marks for q in exam.questions)
    
    if total_students > 0:
        avg_score = sum(r.total_score for r in student_results) / total_students
        avg_percentage = (avg_score / max_possible_score) * 100 if max_possible_score > 0 else 0
    else:
        avg_score = 0
        avg_percentage = 0
    
    return render_template('admin_exam_results.html',
                         exam=exam,
                         student_results=student_results,
                         total_students=total_students,
                         total_questions=total_questions,
                         max_possible_score=max_possible_score,
                         avg_score=avg_score,
                         avg_percentage=avg_percentage)

@app.route('/admin/student_results/<int:exam_id>/<int:student_id>')
@login_required
def admin_student_results(exam_id, student_id):
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('admin_dashboard'))
    
    exam = Exam.query.get_or_404(exam_id)
    student = User.query.get_or_404(student_id)
    
    # Get detailed results for this student
    results = Result.query.filter_by(
        exam_id=exam_id, 
        student_id=student_id
    ).options(db.joinedload(Result.question)).order_by(Result.question_id).all()
    
    if not results:
        flash('No results found for this student.', 'error')
        return redirect(url_for('admin_exam_results', exam_id=exam_id))
    
    total_score = sum(result.marks_awarded for result in results)
    max_possible = sum(result.question.max_marks for result in results if result.question)
    
    return render_template('admin_student_results.html',
                         exam=exam,
                         student=student,
                         results=results,
                         total_score=total_score,
                         max_possible=max_possible)

@app.route('/admin/delete_exam/<int:exam_id>')
@login_required
def delete_exam(exam_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    exam = Exam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    
    flash('Exam deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/evaluator_config', methods=['GET', 'POST'])
@login_required
def evaluator_config():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        try:
            # Get form data
            evaluator_type = request.form.get('evaluator_type', 'ai')
            pass_threshold = float(request.form.get('pass_threshold', 2.5))
            excellent_threshold = float(request.form.get('excellent_threshold', 4.0))
            good_threshold = float(request.form.get('good_threshold', 3.0))
            fair_threshold = float(request.form.get('fair_threshold', 2.0))
            irrelevance_threshold = float(request.form.get('irrelevance_threshold', 0.15))
            critical_word_penalty_threshold = float(request.form.get('critical_word_penalty_threshold', 0.8))
            sas_threshold = float(request.form.get('sas_threshold', 0.25))
            
            # Update configuration
            from evaluator_config import update_config
            update_config(
                default_evaluator_type=evaluator_type,
                evaluation_thresholds={
                    'pass_threshold': pass_threshold,
                    'excellent_threshold': excellent_threshold,
                    'good_threshold': good_threshold,
                    'fair_threshold': fair_threshold,
                    'irrelevance_threshold': irrelevance_threshold,
                    'critical_word_penalty_threshold': critical_word_penalty_threshold,
                    'sas_threshold': sas_threshold
                }
            )
            
            flash('Evaluator configuration updated successfully!', 'success')
            return redirect(url_for('evaluator_config'))
            
        except Exception as e:
            flash(f'Error updating configuration: {str(e)}', 'error')
    
    # Get current configuration
    config = get_evaluator_config()
    thresholds = config.get('evaluation_thresholds', {})
    
    return render_template('evaluator_config.html', 
                         config=config, 
                         thresholds=thresholds)

# Student Routes
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied. Student privileges required.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if not current_user.department_id:
        flash('You are not assigned to any department. Please contact admin.', 'warning')
        return render_template('student_dashboard.html', 
                             available_exams=[], 
                             completed_exams=[])
    
    # Show only exams from student's department that are enabled and active
    available_exams = Exam.query.filter_by(
        department_id=current_user.department_id,
        is_enabled=True,
        is_active=True
    ).all()
    
    # Show completed exams from student's department
    completed_exams = db.session.query(Exam).join(Result).filter(
        Result.student_id == current_user.id,
        Exam.department_id == current_user.department_id
    ).distinct().all()
    
    return render_template('student_dashboard.html', 
                         available_exams=available_exams,
                         completed_exams=completed_exams)

def auto_submit_exam_answers(exam_id, student_id, session_id):
    """Auto-submit exam answers when time expires."""
    try:
        # Check if already submitted
        existing_result = Result.query.filter_by(
            exam_id=exam_id, 
            student_id=student_id
        ).first()
        
        if existing_result:
            return  # Already submitted
        
        # Get exam and questions
        exam = Exam.query.get_or_404(exam_id)
        questions = Question.query.filter_by(exam_id=exam_id).all()
        
        # Get any saved answers from localStorage (we'll simulate this by checking for partial answers)
        # In a real implementation, you might want to store answers in the database as they're typed
        # For now, we'll just mark the session as completed without answers
        
        # Create a result record indicating auto-submission
        result = Result(
            exam_id=exam_id,
            student_id=student_id,
            question_id=questions[0].id if questions else None,  # Use first question or None
            student_answer="[Auto-submitted due to time expiration]",
            marks_awarded=0,
            ai_score=0.0,
            submitted_at=datetime.utcnow()
        )
        db.session.add(result)
        
        print(f"Auto-submitted exam {exam_id} for student {student_id}")
        
    except Exception as e:
        print(f"Error in auto-submit: {str(e)}")
        # Don't raise the exception to avoid breaking the main flow

@app.route('/student/exam/<int:exam_id>')
@login_required
def take_exam(exam_id):
    if current_user.role != 'student':
        flash('Access denied. Student privileges required.', 'error')
        return redirect(url_for('student_dashboard'))
    
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if exam is available for this student
    if not exam.is_enabled or not exam.is_active:
        flash('This exam is not currently available.', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Check if student is in the correct department
    if exam.department_id != current_user.department_id:
        flash('You are not authorized to take this exam.', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Check if exam time has expired
    if exam.end_time and datetime.utcnow() > exam.end_time:
        flash('This exam has already ended.', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Check if student already has a session for this exam
    existing_session = ExamSession.query.filter_by(
        exam_id=exam_id, 
        student_id=current_user.id
    ).first()
    
    if existing_session:
        if existing_session.is_completed:
            flash('You have already completed this exam.', 'info')
            return redirect(url_for('view_results', exam_id=exam_id))
        else:
            # Continue existing session
            time_elapsed = (datetime.utcnow() - existing_session.start_time).total_seconds() / 60
            time_remaining = max(0, exam.duration_minutes - time_elapsed)
            
            if time_remaining <= 0:
                # Time expired, auto-submit the exam
                existing_session.is_completed = True
                existing_session.end_time = datetime.utcnow()
                
                # Auto-submit any answers that were provided
                auto_submit_exam_answers(exam_id, current_user.id, existing_session.id)
                
                db.session.commit()
                flash('Your exam time has expired and has been automatically submitted.', 'warning')
                return redirect(url_for('view_results', exam_id=exam_id))
    else:
        # Create new exam session
        existing_session = ExamSession(
            exam_id=exam_id,
            student_id=current_user.id,
            start_time=datetime.utcnow()
        )
        db.session.add(existing_session)
        db.session.commit()
        
        time_remaining = exam.duration_minutes
    
    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.question_order).all()
    return render_template('exam_interface.html', 
                         exam=exam, 
                         questions=questions,
                         session=existing_session,
                         time_remaining=int(time_remaining))

@app.route('/student/exam/<int:exam_id>/time_remaining')
@login_required
def get_exam_time_remaining(exam_id):
    """Get remaining time for an exam."""
    if current_user.role != 'student':
        return jsonify({'error': 'Access denied'}), 403
    
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if exam is active
    if not exam.is_active:
        return jsonify({'error': 'Exam not active'}), 400
    
    # Get or create exam session
    existing_session = ExamSession.query.filter_by(
        exam_id=exam_id,
        student_id=current_user.id,
        is_completed=False
    ).first()
    
    if not existing_session:
        return jsonify({'error': 'No active session'}), 400
    
    # Calculate remaining time
    time_elapsed = (datetime.utcnow() - existing_session.start_time).total_seconds() / 60
    time_remaining = max(0, exam.duration_minutes - time_elapsed)
    
    return jsonify({
        'time_remaining': int(time_remaining),
        'exam_duration': exam.duration_minutes,
        'session_start': existing_session.start_time.isoformat()
    })

@app.route('/student/submit_exam', methods=['POST'])
@login_required
def submit_exam():
    if current_user.role != 'student':
        return jsonify({'error': 'Access denied'}), 403
    
    exam_id = request.form.get('exam_id')
    exam = Exam.query.get_or_404(exam_id)
    
    if not exam.is_enabled:
        return jsonify({'error': 'Exam not available'}), 400
    
    # Check if already submitted
    existing_result = Result.query.filter_by(
        exam_id=exam_id, 
        student_id=current_user.id
    ).first()
    
    if existing_result:
        return jsonify({'error': 'Exam already submitted'}), 400
    
    try:
        total_score = 0
        questions = Question.query.filter_by(exam_id=exam_id).all()
        
        for question in questions:
            student_answer = request.form.get(f'answer_{question.id}', '')
            
            if student_answer.strip():
                # Check if evaluator is available
                if ai_evaluator is None:
                    return jsonify({'error': 'AI Evaluator not available. Please contact administrator.'}), 500
                
                try:
                    # Evaluate using the selected evaluator
                    result = ai_evaluator.evaluate(
                        student_answer=student_answer,
                        reference_answer=question.reference_answer
                    )
                    
                    # Handle different result formats from different evaluators
                    if 'final_score' in result:
                        # Standard evaluator format (AIEvaluator, OptimizedSAS, etc.)
                        ai_score = result['final_score'] / 10.0  # Convert 0-10 to 0-1
                        details = result['details']
                        
                        # Determine evaluator type for logging
                        evaluator_name = type(ai_evaluator).__name__
                        
                        # Log evaluation details for debugging
                        print(f"🔍 Question {question.id} Evaluation ({evaluator_name}):")
                        print(f"   📊 Final Score: {result['final_score']:.2f}/10")
                        
                        # Different details based on evaluator type
                        if evaluator_name == "OptimizedSASEvaluator":
                            print(f"   🎯 Raw Score: {details.get('raw_score', 0):.4f}")
                            print(f"   📋 Category: {details.get('category', 'Unknown')}")
                            print(f"   🚫 Filtered: {details.get('filtered', False)}")
                            print(f"   ⚙️  Threshold: {details.get('threshold', 0):.3f}")
                        else:
                            # AIEvaluator or other formats
                            print(f"   📏 Length Score: {details.get('length_score', 0):.3f}")
                            print(f"   🧠 Semantic Bi: {details.get('semantic_bi', 0):.3f}")
                            print(f"   🎯 Cross Encoder: {details.get('cross_encoder', 0):.3f}")
                            print(f"   🔑 Keyword Score: {details.get('keyword_score', 0):.3f}")
                            print(f"   💡 Concept Score: {details.get('concept_score', 0):.3f}")
                            if details.get('irrelevant', False):
                                print(f"   ⚠️  Marked as irrelevant")
                        
                    else:
                        # Legacy CleanEvaluator format (fallback)
                        ai_score = result['score']
                        print(f"🔍 Question {question.id} Evaluation (CleanEvaluator):")
                        print(f"   📊 Score: {ai_score:.3f}")
                        print(f"   🎯 Confidence: {result.get('confidence', 0):.3f}")
                        print(f"   🧠 Semantic: {result.get('semantic_similarity', 0):.3f}")
                        print(f"   📝 Linguistic: {result.get('linguistic_quality', 0):.3f}")
                        print(f"   📚 Content: {result.get('content_coverage', 0):.3f}")
                        print(f"   ✨ Text Quality: {result.get('text_quality', 0):.3f}")
                    
                    # Calculate marks based on AI evaluation score
                    marks_awarded = ai_score * question.max_marks
                    
                    total_score += marks_awarded
                    
                    # Save result
                    result = Result(
                        exam_id=exam_id,
                        student_id=current_user.id,
                        question_id=question.id,
                        student_answer=student_answer,
                        ai_score=ai_score,
                        marks_awarded=marks_awarded
                    )
                    db.session.add(result)
                    
                except Exception as e:
                    return jsonify({'error': f'Evaluation failed: {str(e)}'}), 500
        
        db.session.commit()
        
        return jsonify({
            'message': 'Exam submitted successfully!',
            'total_score': round(total_score, 2),
            'redirect_url': url_for('view_results', exam_id=exam_id)
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error submitting exam: {str(e)}'}), 500

@app.route('/student/results/<int:exam_id>')
@login_required
def view_results(exam_id):
    if current_user.role != 'student':
        flash('Access denied. Student privileges required.', 'error')
        return redirect(url_for('student_dashboard'))
    
    exam = Exam.query.get_or_404(exam_id)
    
    # Get results with proper relationship loading
    results = Result.query.filter_by(
        exam_id=exam_id, 
        student_id=current_user.id
    ).options(db.joinedload(Result.question)).order_by(Result.question_id).all()
    
    if not results:
        flash('No results found for this exam.', 'error')
        return redirect(url_for('student_dashboard'))
    
    total_score = sum(result.marks_awarded for result in results)
    
    # Calculate max possible marks safely
    max_possible = 0
    for result in results:
        if result.question:
            max_possible += result.question.max_marks
        else:
            # Fallback: get question directly if relationship fails
            question = Question.query.get(result.question_id)
            if question:
                max_possible += question.max_marks
    
    return render_template('results.html', 
                         exam=exam, 
                         results=results, 
                         total_score=total_score,
                         max_possible=max_possible)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default departments
        departments_data = [
            {'name': 'ITS', 'description': 'ITS'},
            {'name': 'LTS', 'description': 'LTS'},
            {'name': 'BLS', 'description': 'BLS'},
            {'name': 'LES', 'description': 'LES'}
        ]
        
        # Only create if no departments exist at all
        if Department.query.count() == 0:
            for dept_data in departments_data:
                dept = Department(name=dept_data['name'], description=dept_data['description'])
                db.session.add(dept)
        
        db.session.commit()
        
        # Get departments for assigning students
        its_dept = Department.query.filter_by(name='ITS').first()
        lts_dept = Department.query.filter_by(name='LTS').first()
        bls_dept = Department.query.filter_by(name='BLS').first()
        les_dept = Department.query.filter_by(name='LES').first()
        
        # Ensure default users exist
        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)
        
        # Create students - 2 in each department (8 total)
        students_data = [
            # ITS Department
            {'username': 'its1', 'dept': its_dept},
            {'username': 'its2', 'dept': its_dept},
            # LTS Department  
            {'username': 'lts1', 'dept': lts_dept},
            {'username': 'lts2', 'dept': lts_dept},
            # BLS Department
            {'username': 'bls1', 'dept': bls_dept},
            {'username': 'bls2', 'dept': bls_dept},
            # LES Department
            {'username': 'les1', 'dept': les_dept},
            {'username': 'les2', 'dept': les_dept}
        ]
        
        for student_data in students_data:
            username = student_data['username']
            dept = student_data['dept']
            if not User.query.filter_by(username=username).first():
                db.session.add(User(
                    username=username,
                    password=generate_password_hash(f'{username}123'),
                    role='student',
                    department_id=dept.id if dept else None
                ))
        
        db.session.commit()
        print("Default departments and users ensured:")
        print("Departments: ITS, LTS, BLS, LES")
        print("Admin: username=admin, password=admin123")
        print("Students (2 per department):")
        print("  ITS: its1/its1123, its2/its2123")
        print("  LTS: lts1/lts1123, lts2/lts2123") 
        print("  BLS: bls1/bls1123, bls2/bls2123")
        print("  LES: les1/les1123, les2/les2123")
    
    app.run(debug=True, host='0.0.0.0', port=5002)
