from flask import Flask, render_template, redirect, url_for, session, request, jsonify

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String

from random import randint
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "any-string-you-want-just-keep-it-secret"
# !If not exists !
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///website.db"


# Creates a basic class
class Base(DeclarativeBase):
    pass


# Creates the db
db = SQLAlchemy(model_class=Base)
# Binds the db with flask app
db.init_app(app)


# sets the table/model structure


class User(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True,  autoincrement=True)
    username: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    city: Mapped[str] = mapped_column(String(250), unique=False, nullable=False)
    password: Mapped[str] = mapped_column(String(250), unique=False, nullable=False)
    api_key: Mapped[str] = mapped_column(String(250), unique=False, nullable=False)
 

# Create table schema in the db
# !Comment after creating a table!
# with app.app_context():
#     db.create_all()

class CreateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    submit = SubmitField('Submit')


class APISubmitForm(FlaskForm):
    submit = SubmitField('Get API-key')

# --- API funcs ---

@app.route('/api', methods=['GET', 'POST'])
def api():
    form = APISubmitForm()
    if request.method == 'POST':
        with app.app_context():
            user = User.query.filter_by(username=session.get('username')).first()
            if not ('None' in user.api_key):
                api_key = user.api_key
            else:
                api_key = create_api_key()
                user.api_key = api_key

            db.session.commit()
            return render_template('api.html', username=session.get('username'), form=form, api_key=api_key)

        with app.app_context():
            user = User.query.filter_by(username=session.get('username')).first()
            user.api_key = api_key
            db.session.commit()
        return render_template('api.html', username=session.get('username'), form=form, message=message)
    return render_template('api.html', username=session.get('username'), form=form)


    



@app.route('/')
def home():
    action = request.args.get('action')
    if action == 'login':
        return render_template('index.html', login=True)
    elif action == 'create_account':
        return render_template('index.html', create_account=True)
    return render_template('index.html')




@app.route('/projects')
def projects():
    return render_template('projects.html')

# @app.route('/test')
# def test():
#     return render_template('test.html')


# --- Login page funcs ---
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.args.get('exists') == 'True':
        if_exists = True
    else:
        if_exists = False
    form = CreateAccountForm()
    if form.validate_on_submit():
        session["username"] = form.username.data
        session["password"] = form.password.data
        session["city"] = form.city.data


        if if_exists:
            with app.app_context():
                user = User.query.filter_by(username = session.get('username')).first()
                if user:
                    if check_password_hash(user.password, session.get('password')):
                        return redirect(url_for('home', action='login'))
                    else:
                        return render_template('login.html', form=form, if_exists=if_exists, password_not_match=True)
                else:
                    return render_template('login.html', form=form, if_exists=if_exists, no_username=True)
            db.session.commit()

        elif if_exists == False:
            if check_if_user_exists(session.get("username")) == False:
                add_user(username=session.get('username'), password=hash_password(session.get('password')), city=session.get('city'))
            else:
                return 'User already exists'
            return redirect(url_for('home', action='create_account'))
    return render_template('login.html', form=form, if_exists=if_exists)







# -- main funcs --
def create_api_key() -> str:
    return fr"{''.join([chr(randint(97, 123)) for _ in range(15)])}${''.join([str(randint(0,9)) for _ in range(15)])}"

def add_user(username: str, password: str, city: str, api_key: str = 'None') -> None:
    with app.app_context():
        new_user = User(username=username, city=city, password=password, api_key=api_key)
        db.session.add(new_user)
        db.session.commit()

    

def get_objects(table: type):
    with app.app_context():
        objects = table.query.all()
        db.session.commit()
    return objects
    
def check_if_user_exists(username_to_check: str) -> bool: 
    with app.app_context():  
        return User.query.filter_by(username = username_to_check).first() != None


def hash_password(password: str) -> str:
    return generate_password_hash(password=password, method='pbkdf2:sha256:1000000', salt_length=8)



'''@app.route('/download')
def download():
    return send_from_directory('static', path="files/cheat_sheet.pdf")'''



if __name__ == '__main__':
    app.run(debug=True)
    