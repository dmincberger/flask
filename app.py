import wtforms
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bs4 import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, SelectField, FileField,HiddenField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileAllowed
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os
from datetime import datetime

# konfiguracja aplikacji
app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = 'ghjk56789)(*&^%ERTYUIIHGFGHJ'
bcrypt = Bcrypt(app)
app.config['UPLOAD_PATH'] = 'uploads'
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.txt']
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 #16MB

# konfiguracja bazy danych
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data/users.sqlite')
db = SQLAlchemy(app)

# tabela bazy danych
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(20))
    lastName = db.Column(db.String(30))
    userMail = db.Column(db.String(50), unique=True)
    userPass = db.Column(db.String(50))
    userRole = db.Column(db.String(20))

    def is_authenticated(self):
        return True

class Folders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_folder = db.Column(db.String(1000))
    folderName = db.Column(db.String(50), unique=True)
    type = db.Column(db.String(20))
    icon = db.Column(db.String(20))
    time = db.Column(db.String(20))

class Files(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_folder = db.Column(db.String(1000))
    fileName = db.Column(db.String(50), unique=True)
    type = db.Column(db.String(20))
    icon = db.Column(db.String(20))
    time = db.Column(db.String(20))
    size = db.Column(db.String(20))

# konfiguracja Flask-Login
loginManager = LoginManager()
loginManager.init_app(app)
loginManager.login_view = 'login'
loginManager.login_message = 'Nie jesteś zalogowany'
loginManager.login_message_category = 'warning'

@loginManager.user_loader
def loadUser(id):
    return Users.query.filter_by(id=id).first()

# formularze
class Login(FlaskForm):
    """formularz logowania"""
    userMail = EmailField('Mail', validators=[DataRequired()], render_kw={'placeholder': 'Mail'})
    userPass = PasswordField('Hasło', validators=[DataRequired()], render_kw={'placeholder': 'Hasło'})
    submit = SubmitField('Zaloguj')

class Register(FlaskForm):
    """formularz rejestracji"""
    firstName = StringField('Imię', validators=[DataRequired()], render_kw={'placeholder': 'Imię'})
    lastName = StringField('Nazwisko', validators=[DataRequired()], render_kw={'placeholder': 'Nazwisko'})
    userMail = EmailField('Mail', validators=[DataRequired()], render_kw={'placeholder': 'Mail'})
    userPass = PasswordField('Hasło', validators=[DataRequired()], render_kw={'placeholder': 'Hasło'})
    submit = SubmitField('Rejestruj')

class rename_folder(FlaskForm):
    """formularz zmiany nazwy"""
    new_name = StringField('nowa_nazwa', validators=[DataRequired()], render_kw={'placeholder': 'Nowa_nazwa'})
    submit = SubmitField('Zmien nazwe')

class rename_file(FlaskForm):
    new_name = StringField('nowa_nazwa', validators=[DataRequired()], render_kw={'placeholder': 'Nowa_nazwa'})
    submit = SubmitField('Zmien nazwe')

class delete_folder(FlaskForm):
    submit = SubmitField('USUN')

class delete_file(FlaskForm):
    submit = SubmitField('USUN')

class Add(FlaskForm):
    """formularz dodawania użytkowników"""
    firstName = StringField('Imię', validators=[DataRequired()], render_kw={'placeholder': 'Imię'})
    lastName = StringField('Nazwisko', validators=[DataRequired()], render_kw={'placeholder': 'Nazwisko'})
    userMail = EmailField('Mail', validators=[DataRequired()], render_kw={'placeholder': 'Mail'})
    userPass = PasswordField('Hasło', validators=[DataRequired()], render_kw={'placeholder': 'Hasło'})
    userRole = SelectField('Uprawnienia', validators=[DataRequired()], choices=[('user', 'Użytkownik'), ('admin', 'Administrator')])
    submit = SubmitField('Dodaj')

class Edit(FlaskForm):
    """formularz dodawania użytkowników"""
    firstName = StringField('Imię', validators=[DataRequired()], render_kw={'placeholder': 'Imię'})
    lastName = StringField('Nazwisko', validators=[DataRequired()], render_kw={'placeholder': 'Nazwisko'})
    userMail = EmailField('Mail', validators=[DataRequired()], render_kw={'placeholder': 'Mail'})
    userRole = SelectField('Uprawnienia', validators=[DataRequired()], choices=[('user', 'Użytkownik'), ('admin', 'Administrator')])
    submit = SubmitField('Zapisz')

class Password(FlaskForm):
    """formularz zmiany hasła przez zalogowanych użytkowników"""
    userMail = EmailField('Mail', validators=[DataRequired()], render_kw={'placeholder': 'Mail'})
    userPass = PasswordField('Bieżące hasło', validators=[DataRequired()], render_kw={'placeholder': 'Bieżące hasło'})
    newUserPass = PasswordField('Nowe hasło', validators=[DataRequired()], render_kw={'placeholder': 'Nowe hasło'})
    submit = SubmitField('Zapisz')

class ChangePass(FlaskForm):
    """formularz zmiany hasła przez administratora"""
    userPass = PasswordField('Hasło', validators=[DataRequired()], render_kw={'placeholder': 'Hasło'})
    submit = SubmitField('Zapisz')

class Search(FlaskForm):
    """formularz wysukiwania plików i folderów"""
    searchKey = StringField('Szukaj', validators=[DataRequired()])
    submit = SubmitField('Szukaj')

class CreateFolders(FlaskForm):
    """formularz tworzenia nowego folderu"""
    folderName = StringField('Nazwa folderu', validators=[DataRequired()], render_kw={'placeholder': 'Nazwa folderu'})
    submit = SubmitField('Utwórz')

class UploadFiles(FlaskForm):
    """formularz do przesyłania pliku"""
    fileName = FileField('Nazwa pliku', validators=[FileAllowed(app.config['UPLOAD_EXTENSIONS'])])
    submit = SubmitField('Prześlij')

# główna aplikacja
@app.route('/')
def index():
    return render_template('index.html', title='Home', headline='Zarządzanie użytkownikami')

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = Users.query.all()
    if not user:
        return redirect(url_for('register'))
    else:
        loginForm = Login()
        if loginForm.validate_on_submit():
            user = Users.query.filter_by(userMail=loginForm.userMail.data).first()
            if user:
                if bcrypt.check_password_hash(user.userPass, loginForm.userPass.data):
                    login_user(user)
                    return redirect(url_for('dashboard'))
    return render_template('login.html', title='Logowanie', headline='Logowanie', loginForm=loginForm)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    registerForm = Register()
    user = Users.query.all()
    if registerForm.validate_on_submit() and not user:
        try:
            hashPass = bcrypt.generate_password_hash(registerForm.userPass.data)
            newUser = Users(userMail=registerForm.userMail.data, userPass=hashPass, firstName=registerForm.firstName.data, lastName=registerForm.lastName.data, userRole='admin')
            db.session.add(newUser)
            db.session.commit()
            flash('Konto utworzone poprawnie', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Taki adres mail już istnieje, wpisz inny', 'danger')
            # return redirect(url_for('register'))
    elif registerForm.validate_on_submit():
        try:
            hashPass = bcrypt.generate_password_hash(registerForm.userPass.data)
            newUser = Users(userMail=registerForm.userMail.data, userPass=hashPass, firstName=registerForm.firstName.data, lastName=registerForm.lastName.data, userRole='user')
            db.session.add(newUser)
            db.session.commit()
            flash('Konto utworzone poprawnie', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Taki adres mail już istnieje, wpisz inny', 'danger')
            # return redirect(url_for('register'))
    return render_template('register.html', title='Rejestracja', headline='Rejestracja', registerForm=registerForm)

@app.route('/dashboard')
@login_required
def dashboard():
    users = Users.query.all()
    folders = Folders.query.filter_by(parent_folder=app.config['UPLOAD_PATH'])
    files = Files.query.filter_by(parent_folder=app.config['UPLOAD_PATH'])
    addUser = Add()
    editUser = Edit()
    editUserPass = ChangePass()
    search = Search()
    createFolder = CreateFolders()
    uploadFile = UploadFiles()
    renameFolder = rename_folder()
    deleteFolder = delete_folder()
    deleteFile = delete_file()
    renameFile = rename_file()
    return render_template('dashboard.html', title='Dashboard', users=users, addUser=addUser, editUser=editUser, editUserPass=editUserPass, search=search, createFolder=createFolder, uploadFile=uploadFile, renameFolder=renameFolder, deleteFolder=deleteFolder,folders=folders, files=files, deleteFile=deleteFile,renameFile=renameFile)

@app.route('/add-user', methods=['POST', 'GET'])
@login_required
def addUser():
    addUser = Add()
    if addUser.validate_on_submit():
        try:
            hashPass = bcrypt.generate_password_hash(addUser.userPass.data)
            newUser = Users(userMail=addUser.userMail.data, userPass=hashPass, firstName=addUser.firstName.data, lastName=addUser.lastName.data, userRole=addUser.userRole.data)
            db.session.add(newUser)
            db.session.commit()
            flash('Konto utworzone poprawnie', 'success')
            return redirect(url_for('dashboard'))
        except Exception:
            flash('Taki adres mail już istnieje, wpisz inny', 'danger')
            return redirect(url_for('dashboard'))

@app.route('/edit-user<int:id>', methods=['POST', 'GET'])
@login_required
def editUser(id):
    editUser = Edit()
    user = Users.query.get_or_404(id)
    if editUser.validate_on_submit():
        user.firstName = editUser.firstName.data
        user.lastName = editUser.lastName.data
        user.userMail = editUser.userMail.data
        user.userRole = editUser.userRole.data
        db.session.commit()
        flash('Dane zapisane poprawnie', 'success')
        return redirect(url_for('dashboard'))

@app.route('/delete-user', methods=['POST', 'GET'])
@login_required
def deleteUser():
    if request.method == 'GET':
        id = request.args.get('id')
        user = Users.query.filter_by(id=id).one()
        db.session.delete(user)
        db.session.commit()
        flash('Użytkownik usunięty poprawnie', 'success')
        return redirect(url_for('dashboard'))

@app.route('/change-pass', methods=['GET', 'POST'])
@login_required
def changePass():
    changePassForm = Password()
    if changePassForm.validate_on_submit():
        user = Users.query.filter_by(userMail=changePassForm.userMail.data).first()
        if user:
            if bcrypt.check_password_hash(user.userPass, changePassForm.userPass.data):
                user.userPass = bcrypt.generate_password_hash(changePassForm.newUserPass.data)
                db.session.commit()
                flash('Hasło zostało zmienione', 'success')
                return redirect(url_for('dashboard'))
    return render_template('change-pass.html', title='Zmiana hasła', changePassForm=changePassForm)

@app.route('/edit-user-pass<int:id>', methods=('GET', 'POST'))
@login_required
def editUserPass(id):
    editUserPass = ChangePass()
    user = Users.query.get_or_404(id)
    if editUserPass.validate_on_submit():
        user.userPass = bcrypt.generate_password_hash(editUserPass.userPass.data)
        db.session.commit()
        flash('Hasło zostało zmienione', 'success')
        return redirect(url_for('dashboard'))

@app.route('/create-folder', methods=('GET', 'POST'))
@login_required
def createFolder():
    folderName = request.form['folderName']
    if folderName != '':
        os.mkdir(os.path.join(app.config['UPLOAD_PATH'], folderName))
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        newFolder = Folders(folderName=folderName, type='folder', icon='bi bi-folder', time=time, parent_folder=app.config['UPLOAD_PATH'])
        db.session.add(newFolder)
        db.session.commit()
        flash('Folder utworzony poprawnie', 'success')
        return redirect(url_for('dashboard'))

@app.route('/rename-folder<string:old_name>', methods=['GET', 'POST'])
@login_required
def renameFolder(old_name):
    new_folder_name = request.form['new_name']
    current_path = os.getcwd()
    if new_folder_name == '':
        flash('Prosze podac jakas nazwe folderu', 'danger')
        return redirect(url_for('dashboard'))
    if os.path.exists(os.path.join(app.config['UPLOAD_PATH'], new_folder_name)):
        print(old_name)
        print(new_folder_name)
        flash('ten folder juz istnieje', 'danger')
        return redirect(url_for('dashboard'))
    renamed_folder = Folders.query.filter_by(folderName=old_name).first()
    renamed_folder.folderName = new_folder_name
    os.rename(os.path.join(current_path,app.config['UPLOAD_PATH'], old_name), os.path.join(current_path,app.config['UPLOAD_PATH'], new_folder_name))
    db.session.commit()

    return redirect(url_for('dashboard'))

@app.route('/rename-file<string:old_name>', methods=['GET','POST'])
@login_required
def rename_file_function(old_name):
    new_file_name = request.form['new_name']
    current_path = os.getcwd()
    if new_file_name == '':
        flash('Prosze podac jakas nazwe pliku', 'danger')
        return redirect(url_for('dashboard'))
    if os.path.exists(os.path.join(app.config['UPLOAD_PATH'], new_file_name)):
        print(old_name)
        print(new_file_name)
        flash('ten folder juz istnieje', 'danger')
        return redirect(url_for('dashboard'))
    renamed_file = Files.query.filter_by(fileName=old_name).first()
    renamed_file.fileName = new_file_name
    os.rename(os.path.join(current_path, app.config['UPLOAD_PATH'], old_name),
              os.path.join(current_path, app.config['UPLOAD_PATH'], new_file_name))
    db.session.commit()

    return redirect(url_for('dashboard'))

@app.route('/remove-folder<string:folder_name>', methods=['GET', 'POST'])
@login_required
def removeFolder(folder_name):
    Folders.query.filter_by(folderName=folder_name).delete()
    db.session.commit()
    current_path = os.getcwd()
    os.rmdir(os.path.join(current_path,app.config['UPLOAD_PATH'], folder_name))
    return redirect(url_for('dashboard'))

@app.route('/upload-file', methods=('GET', 'POST'))
@login_required
def uploadFile():
    uploadedFile = request.files['fileName']
    fileName = secure_filename(uploadedFile.filename)
    if fileName != '':
        fileExtension = os.path.splitext(fileName)[1]
        if fileExtension not in app.config['UPLOAD_EXTENSIONS']:
            abort(400)
        type = ''
        icon = ''
        if fileExtension == '.png':
            type = 'png'
            icon = 'bi bi-filetype-png'
        elif fileExtension == '.jpg':
            type = 'jpg'
            icon = 'bi bi-filetype-jpg'
        elif fileExtension == '.jpeg':
            type = 'jpeg'
            icon = 'bi bi-filetype-jpg'
        elif fileExtension == '.txt':
            type = 'txt'
            icon = 'bi bi-filetype-txt'
        uploadedFile.save(os.path.join(app.config['UPLOAD_PATH'], fileName))
        size = round(os.stat(os.path.join(app.config['UPLOAD_PATH'], fileName)).st_size / (1024 * 1024), 2)
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        newFile = Files(fileName=fileName, type=type, icon=icon, time=time, size=size,parent_folder=app.config['UPLOAD_PATH'])
        db.session.add(newFile)
        db.session.commit()
        flash('Plik przesłany poprawnie', 'success')
        return redirect(url_for('dashboard'))

@app.route('/delete-file<string:file_name>', methods=('GET', 'POST'))
@login_required
def remove_file(file_name):
    print("HALO FILE-NAME:"+str(file_name))
    Files.query.filter_by(fileName=file_name).delete()
    db.session.commit()
    current_path = os.getcwd()
    os.remove(os.path.join(current_path,app.config['UPLOAD_PATH'], file_name))
    return redirect(url_for('dashboard'))

@app.route('/change-folder', methods=('GET','POST'))
@login_required
def traverse_folder():
    if request.method == 'GET':
        name = request.args.get('name')
        app.config['UPLOAD_PATH'] += "/"+name
        return redirect(url_for('dashboard'))
@app.route('/go-back', methods=('GET','POST'))
@login_required
def traverse_back():
    if app.config['UPLOAD_PATH'] == "uploads":
        return redirect(url_for('dashboard'))
    upload_split = app.config['UPLOAD_PATH'].split("/")
    del upload_split[-1]
    seperator = "/"
    new_path = seperator.join(upload_split)
    app.config['UPLOAD_PATH'] = new_path
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)