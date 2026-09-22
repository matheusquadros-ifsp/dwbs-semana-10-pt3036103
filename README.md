# Aula 060.C. Funções, listagem, contadores e e-mail

Mesmo funcionamento da versão anterior (formulário nome + função, listagens,
contadores). Adicionado: a cada novo usuário cadastrado (não reenvio de um
já existente), um e-mail é disparado via SendGrid (relay SMTP) para
`flaskaulasweb@zohomail.com` e `matheus.quadros@aluno.ifsp.edu.br`.

## Antes do deploy

Crie um arquivo `.env` na raiz do projeto (mesmo nível do `hello.py`) com:

```
API_KEY=sua_api_key_do_sendgrid
```

(`.env` está no `.gitignore` — não sobe pro Git. Veja `.env.example`.)

**Importante:** o remetente configurado é `flaskaulasweb@zohomail.com`. Esse
endereço precisa estar verificado no SendGrid (Single Sender Verification ou
domínio autenticado), senão o envio falha — mas isso não derruba o cadastro:
o erro só é logado (aba Web → Error log).

## Deploy no PythonAnywhere

Se já existir `migrations/` ou `data.sqlite` de uma semana anterior, apague:

```bash
rm -rf migrations
rm -f data.sqlite
```

Depois:

```bash
chmod 777 change_repo.sh
./change_repo.sh <link-do-repo>
pip install -r requirements/common.txt
export FLASK_APP=hello.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

Reload na aba **Web**.

## Testar o envio manualmente

```bash
flask shell
>>> send_new_user_notification('Teste')
```
