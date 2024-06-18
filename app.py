from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT
from whoosh.qparser import QueryParser
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aeneta.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Definir el esquema de búsqueda
schema = Schema(
    title=TEXT(stored=True),
    authors=TEXT(stored=True),
    summary=TEXT(stored=True),
    keywords=TEXT(stored=True),
    content=TEXT(stored=True)
)

# Crear el directorio para el índice si no existe
if not os.path.exists("indexdir"):
    os.mkdir("indexdir")

# Crear un índice en el directorio (si ya existe, se abre)
if not os.path.exists("indexdir/index"):
    index = create_in("indexdir", schema)
else:
    index = open_dir("indexdir")

# Definir modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)

class Alumno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    boleta = db.Column(db.String(50), nullable=False)
    area = db.Column(db.String(150), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('alumno', uselist=False))

class Docente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    specialization = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('docente', uselist=False))

class PersonalAdministrativo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    role_description = db.Column(db.String(250), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('admin', uselist=False))

class Sinodal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    specialization = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('sinodal', uselist=False))

class Egresado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    boleta = db.Column(db.String(50), nullable=False)
    area = db.Column(db.String(150), nullable=False)
    generation = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('egresado', uselist=False))

class Convocatoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    start_date = db.Column(db.String(50), nullable=False)
    end_date = db.Column(db.String(50), nullable=False)

class InscripcionConvocatoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    convocatoria_id = db.Column(db.Integer, db.ForeignKey('convocatoria.id'), nullable=False)
    alumno_id = db.Column(db.Integer, db.ForeignKey('alumno.id'), nullable=False)
    convocatoria = db.relationship('Convocatoria', backref=db.backref('inscripciones', cascade='all, delete-orphan'))
    alumno = db.relationship('Alumno', backref=db.backref('inscripciones', cascade='all, delete-orphan'))

# Crear la base de datos y las tablas
with app.app_context():
    db.create_all()
    # Verificar si el usuario 'atzin' ya existe
    if not User.query.filter_by(username='atzin').first():
        # Crear el usuario 'atzin'
        user = User(username='atzin', password='atzin', role='admin')
        db.session.add(user)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ruta para la página principal de búsqueda
@app.route('/')
def home():
    return render_template('index.html')

# Ruta para el login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            flash('Logged in successfully.')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

# Ruta para el logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

# Ruta para procesar la búsqueda
@app.route('/search', methods=['POST'])
@login_required
def search():
    query_str = request.form['query']
    with index.searcher() as searcher:
        query = QueryParser("content", index.schema).parse(query_str)
        results = searcher.search(query)
        return jsonify([{'title': r['title'], 'content': r['content']} for r in results])

# Ruta para la página de registro de formas de titulación
@app.route('/register')
@login_required
def register():
    return render_template('register.html')

# Ruta para procesar el registro de formas de titulación
@app.route('/register', methods=['POST'])
@login_required
def register_post():
    title = request.form['title']
    content = request.form['requirements']
    try:
        writer = index.writer()
        writer.add_document(title=title, content=content)
        writer.commit()
    except Exception as e:
        writer.cancel()
        raise e
    return redirect(url_for('register'))

# Ruta para listar formas de titulación
@app.route('/list_titulaciones')
@login_required
def list_titulaciones():
    titulaciones = []
    with index.searcher() as searcher:
        results = searcher.search(QueryParser("content", index.schema).parse("*"))
        for r in results:
            titulaciones.append({'title': r['title'], 'content': r['content']})
    return render_template('list_titulaciones.html', titulaciones=titulaciones)

# Ruta para la página de registro de egresados
@app.route('/register_egresado')
@login_required
def register_egresado():
    return render_template('register_egresado.html')

# Ruta para procesar el registro de egresados
@app.route('/register_egresado', methods=['POST'])
@login_required
def register_egresado_post():
    name = request.form['name']
    boleta = request.form['boleta']
    area = request.form['area']
    generation = request.form['generation']
    username = request.form['username']
    password = request.form['password']
    # Verificar si el nombre de usuario ya existe
    if User.query.filter_by(username=username).first():
        flash('El nombre de usuario ya existe. Por favor, elija otro.')
        return redirect(url_for('register_egresado'))
    user = User(username=username, password=password, role='egresado')
    db.session.add(user)
    db.session.commit()
    egresado = Egresado(name=name, boleta=boleta, area=area, generation=generation, user_id=user.id)
    db.session.add(egresado)
    db.session.commit()
    return redirect(url_for('register_egresado'))

# Ruta para listar egresados
@app.route('/list_egresados')
@login_required
def list_egresados():
    egresados = Egresado.query.all()
    return render_template('list_egresados.html', egresados=egresados)

# Ruta para la página de registro del calendario de convocatorias
@app.route('/register_calendar')
@login_required
def register_calendar():
    return render_template('register_calendar.html')

# Ruta para procesar el registro del calendario de convocatorias
@app.route('/register_calendar', methods=['POST'])
@login_required
def register_calendar_post():
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    requirements = request.form['requirements']
    calendarios.append({'start_date': start_date, 'end_date': end_date, 'requirements': requirements})
    return redirect(url_for('register_calendar'))

# Ruta para listar calendarios de convocatorias
@app.route('/list_calendars')
@login_required
def list_calendars():
    return render_template('list_calendars.html', calendarios=calendarios)

# Ruta para la página de registro de convocatorias de titulación
@app.route('/register_call')
@login_required
def register_call():
    return render_template('register_call.html')

# Ruta para procesar el registro de convocatorias de titulación
@app.route('/register_call', methods=['POST'])
@login_required
def register_call_post():
    title = request.form['title']
    description = request.form['description']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    convocatoria = Convocatoria(title=title, description=description, start_date=start_date, end_date=end_date)
    db.session.add(convocatoria)
    db.session.commit()
    return redirect(url_for('register_call'))

# Ruta para listar convocatorias de titulación
@app.route('/list_calls')
@login_required
def list_calls():
    convocatorias = Convocatoria.query.all()
    return render_template('list_calls.html', convocatorias=convocatorias)

# Ruta para la página de registro de seminarios de titulación
@app.route('/register_seminar')
@login_required
def register_seminar():
    return render_template('register_seminar.html')

# Ruta para procesar el registro de seminarios de titulación
@app.route('/register_seminar', methods=['POST'])
@login_required
def register_seminar_post():
    date = request.form['date']
    topic = request.form['topic']
    speaker = request.form['speaker']
    seminarios.append({'date': date, 'topic': topic, 'speaker': speaker})
    return redirect(url_for('register_seminar'))

# Ruta para listar seminarios de titulación
@app.route('/list_seminars')
@login_required
def list_seminars():
    return render_template('list_seminars.html', seminarios=seminarios)

# Ruta para la página de registro de trabajos de titulación
@app.route('/register_thesis')
@login_required
def register_thesis():
    return render_template('register_thesis.html')

# Ruta para procesar el registro de trabajos de titulación
@app.route('/register_thesis', methods=['POST'])
@login_required
def register_thesis_post():
    title = request.form['title']
    authors = request.form['authors']
    summary = request.form['summary']
    keywords = request.form['keywords']
    try:
        writer = index.writer()
        writer.add_document(title=title, authors=authors, summary=summary, keywords=keywords, content=summary)
        writer.commit()
    except Exception as e:
        writer.cancel()
        raise e
    return redirect(url_for('register_thesis'))

# Ruta para la página de registro de alumnos
@app.route('/register_student')
@login_required
def register_student():
    return render_template('register_student.html')

# Ruta para procesar el registro de alumnos
@app.route('/register_student', methods=['POST'])
@login_required
def register_student_post():
    name = request.form['name']
    boleta = request.form['boleta']
    area = request.form['area']
    semester = request.form['semester']
    username = request.form['username']
    password = request.form['password']
    # Verificar si el nombre de usuario ya existe
    if User.query.filter_by(username=username).first():
        flash('El nombre de usuario ya existe. Por favor, elija otro.')
        return redirect(url_for('register_student'))
    user = User(username=username, password=password, role='student')
    db.session.add(user)
    db.session.commit()
    student = Alumno(name=name, boleta=boleta, area=area, semester=semester, user_id=user.id)
    db.session.add(student)
    db.session.commit()
    return redirect(url_for('register_student'))

# Ruta para listar alumnos
@app.route('/list_students')
@login_required
def list_students():
    alumnos = Alumno.query.all()
    return render_template('list_students.html', alumnos=alumnos)

# Ruta para la página de registro de docentes
@app.route('/register_teacher')
@login_required
def register_teacher():
    return render_template('register_teacher.html')

# Ruta para procesar el registro de docentes
@app.route('/register_teacher', methods=['POST'])
@login_required
def register_teacher_post():
    name = request.form['name']
    specialization = request.form['specialization']
    username = request.form['username']
    password = request.form['password']
    # Verificar si el nombre de usuario ya existe
    if User.query.filter_by(username=username).first():
        flash('El nombre de usuario ya existe. Por favor, elija otro.')
        return redirect(url_for('register_teacher'))
    user = User(username=username, password=password, role='teacher')
    db.session.add(user)
    db.session.commit()
    teacher = Docente(name=name, specialization=specialization, user_id=user.id)
    db.session.add(teacher)
    db.session.commit()
    return redirect(url_for('register_teacher'))

# Ruta para listar docentes
@app.route('/list_teachers')
@login_required
def list_teachers():
    docentes = Docente.query.all()
    return render_template('list_teachers.html', docentes=docentes)

# Ruta para la página de registro de personal administrativo
@app.route('/register_admin')
@login_required
def register_admin():
    return render_template('register_admin.html')

# Ruta para procesar el registro de personal administrativo
@app.route('/register_admin', methods=['POST'])
@login_required
def register_admin_post():
    name = request.form['name']
    role_description = request.form['role_description']
    username = request.form['username']
    password = request.form['password']
    # Verificar si el nombre de usuario ya existe
    if User.query.filter_by(username=username).first():
        flash('El nombre de usuario ya existe. Por favor, elija otro.')
        return redirect(url_for('register_admin'))
    user = User(username=username, password=password, role='admin')
    db.session.add(user)
    db.session.commit()
    admin = PersonalAdministrativo(name=name, role_description=role_description, user_id=user.id)
    db.session.add(admin)
    db.session.commit()
    return redirect(url_for('register_admin'))

# Ruta para listar personal administrativo
@app.route('/list_admins')
@login_required
def list_admins():
    admins = PersonalAdministrativo.query.all()
    return render_template('list_admins.html', admins=admins)

# Ruta para la página de registro de sinodales
@app.route('/register_sinodal')
@login_required
def register_sinodal():
    return render_template('register_sinodal.html')

# Ruta para procesar el registro de sinodales
@app.route('/register_sinodal', methods=['POST'])
@login_required
def register_sinodal_post():
    name = request.form['name']
    specialization = request.form['specialization']
    username = request.form['username']
    password = request.form['password']
    # Verificar si el nombre de usuario ya existe
    if User.query.filter_by(username=username).first():
        flash('El nombre de usuario ya existe. Por favor, elija otro.')
        return redirect(url_for('register_sinodal'))
    user = User(username=username, password=password, role='sinodal')
    db.session.add(user)
    db.session.commit()
    sinodal = Sinodal(name=name, specialization=specialization, user_id=user.id)
    db.session.add(sinodal)
    db.session.commit()
    return redirect(url_for('register_sinodal'))

# Ruta para listar sinodales
@app.route('/list_sinodales')
@login_required
def list_sinodales():
    sinodales = Sinodal.query.all()
    return render_template('list_sinodales.html', sinodales=sinodales)

# Ruta para listar convocatorias disponibles para inscripciones
@app.route('/list_available_calls')
@login_required
def list_available_calls():
    convocatorias = Convocatoria.query.all()
    return render_template('list_available_calls.html', convocatorias=convocatorias)

# Ruta para inscribir a un estudiante en una convocatoria
@app.route('/inscribir_convocatoria/<int:convocatoria_id>', methods=['GET', 'POST'])
@login_required
def inscribir_convocatoria(convocatoria_id):
    convocatoria = Convocatoria.query.get_or_404(convocatoria_id)
    if request.method == 'POST':
        if current_user.role != 'student':
            flash('Solo los estudiantes pueden inscribirse en las convocatorias.')
            return redirect(url_for('list_available_calls'))
        alumno = Alumno.query.filter_by(user_id=current_user.id).first()
        inscripcion = InscripcionConvocatoria(convocatoria_id=convocatoria.id, alumno_id=alumno.id)
        db.session.add(inscripcion)
        db.session.commit()
        flash('Inscripción realizada con éxito.')
        return redirect(url_for('list_available_calls'))
    return render_template('inscribir_convocatoria.html', convocatoria=convocatoria)

if __name__ == '__main__':
    app.run(debug=True)
