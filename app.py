from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT
from whoosh.qparser import QueryParser
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Definir el esquema de búsqueda
schema = Schema(
    title=TEXT(stored=True),
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

# Modelo de usuario
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# Diccionario de usuarios simulados
users = {
    'atzin': User(id=1, username='atzin'),
}

@login_manager.user_loader
def load_user(user_id):
    return users.get('atzin') if user_id == '1' else None

# Listas para almacenar datos
egresados = []
calendarios = []

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
        if username == 'atzin' and password == 'atzin':
            user = users['atzin']
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
    egresados.append({'name': name, 'boleta': boleta, 'area': area, 'generation': generation})
    return redirect(url_for('register_egresado'))

# Ruta para listar egresados
@app.route('/list_egresados')
@login_required
def list_egresados():
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
    # Aquí podrías guardar la información en una base de datos o en un archivo
    # Por simplicidad, imprimiremos la información en la consola
    print(f'Título: {title}, Descripción: {description}, Fecha de Inicio: {start_date}, Fecha de Fin: {end_date}')
    return redirect(url_for('register_call'))

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
    # Aquí podrías guardar la información en una base de datos o en un archivo
    # Por simplicidad, imprimiremos la información en la consola
    print(f'Fecha: {date}, Tema: {topic}, Ponente: {speaker}')
    return redirect(url_for('register_seminar'))

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
        writer.add_document(title=title, authors=authors, summary=summary, keywords=keywords)
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
    # Aquí podrías guardar la información en una base de datos o en un archivo
    # Por simplicidad, imprimiremos la información en la consola
    print(f'Nombre: {name}, Boleta: {boleta}, Área: {area}, Semestre Actual: {semester}')
    return redirect(url_for('register_student'))

if __name__ == '__main__':
    app.run(debug=True)
