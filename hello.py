import os
from threading import Thread

from dotenv import load_dotenv
from flask import Flask, render_template, session, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail as SendGridMail

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pt3036103-chave-secreta-dwbs-aula060c'
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Funções fixas que a aplicação sempre garante existir no banco.
DEFAULT_ROLES = ['Administrator', 'Moderator', 'User']

# --- Configuração do envio de e-mail via SendGrid (API HTTP, não SMTP) ---
# A API Key é lida do arquivo .env (variável API_KEY), que NÃO vai para o
# repositório - veja .env.example.
SENDGRID_API_KEY = os.environ.get('API_KEY')
# Remetente: precisa estar verificado no SendGrid (Single Sender
# Verification ou domínio autenticado), senão o envio é rejeitado.
SENDER_EMAIL = 'matheus.quadros@aluno.ifsp.edu.br'
NOTIFICATION_RECIPIENTS = [
    'flaskaulasweb@zohomail.com',
    'matheus.quadros@aluno.ifsp.edu.br',
]
EMAIL_SUBJECT = 'PT3036103 - Matheus Quadros Leal dos Santos'


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


def send_async_email(username):
    """Monta e envia o e-mail via SendGrid (API HTTP).

    Chamável diretamente (ex: no `flask shell`, para testar e ver o
    resultado na hora) ou em uma thread separada (uso normal, para não
    travar a resposta ao usuário enquanto o e-mail é enviado).
    """
    message = SendGridMail(
        from_email=SENDER_EMAIL,
        to_emails=NOTIFICATION_RECIPIENTS,
        subject=EMAIL_SUBJECT,
        plain_text_content='Novo usuário cadastrado: %s' % username,
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        # SendGrid retorna 202 (Accepted) quando o envio é aceito com sucesso.
        print('E-mail enviado. Status code:', response.status_code)
        app.logger.info(
            'E-mail de notificação enviado (status %s).', response.status_code
        )
        return response.status_code == 202
    except Exception as exc:
        print('Erro ao enviar e-mail via SendGrid:', exc)
        app.logger.error('Falha ao enviar e-mail de notificação: %s', exc)
        return False


def send_new_user_notification(username):
    Thread(target=send_async_email, args=(username,)).start()


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Role=Role, User=User,
                send_async_email=send_async_email)


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
