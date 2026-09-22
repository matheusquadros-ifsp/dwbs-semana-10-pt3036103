import os
from threading import Thread

from dotenv import load_dotenv
from flask import Flask, render_template, session, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pt3036103-chave-secreta-dwbs-aula060c'
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# E-mail via relay SMTP do SendGrid. O usuário SMTP do SendGrid é sempre a
# string literal "apikey"; a senha é a API Key gerada no painel do SendGrid,
# lida da variável de ambiente API_KEY (definida em um arquivo .env que NÃO
# vai para o repositório - veja .env.example).
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'
app.config['MAIL_PASSWORD'] = os.environ.get('API_KEY')
app.config['MAIL_DEFAULT_SENDER'] = 'flaskaulasweb@zohomail.com'

bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

# Funções fixas que a aplicação sempre garante existir no banco.
DEFAULT_ROLES = ['Administrator', 'Moderator', 'User']

# Destinatários fixos da notificação de novo cadastro.
NOTIFICATION_RECIPIENTS = [
    'flaskaulasweb@zohomail.com',
    'matheus.quadros@aluno.ifsp.edu.br',
]


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username


class UserForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    role = SelectField('Role?:', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')


def ensure_default_roles():
    """Garante que as 3 funções padrão existam no banco (idempotente)."""
    for role_name in DEFAULT_ROLES:
        if Role.query.filter_by(name=role_name).first() is None:
            db.session.add(Role(name=role_name))
    db.session.commit()


def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as exc:
            # Não deixa uma falha de e-mail (ex: API Key ausente/errada,
            # remetente não verificado no SendGrid) derrubar o cadastro.
            app.logger.error('Falha ao enviar e-mail de notificação: %s', exc)


def send_new_user_notification(username):
    msg = Message(
        subject='PT3036103 - Matheus Quadros Leal dos Santos',
        recipients=NOTIFICATION_RECIPIENTS,
        body='Novo usuário cadastrado: %s' % username,
    )
    Thread(target=send_async_email, args=(app, msg)).start()


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Role=Role, User=User)


@app.route('/', methods=['GET', 'POST'])
def index():
    ensure_default_roles()

    form = UserForm()
    form.role.choices = [
        (role.id, role.name) for role in Role.query.order_by(Role.name).all()
    ]

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            selected_role = Role.query.get(form.role.data)
            user = User(username=form.name.data, role=selected_role)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
            send_new_user_notification(user.username)
        else:
            session['known'] = True
        session['name'] = form.name.data
        return redirect(url_for('index'))

    users = User.query.order_by(User.id).all()
    roles = Role.query.order_by(Role.name).all()

    return render_template(
        'index.html',
        form=form,
        name=session.get('name'),
        known=session.get('known', False),
        users=users,
        roles=roles,
    )


if __name__ == '__main__':
    app.run(debug=True)
