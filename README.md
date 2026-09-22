# Aula 060.C. Funções, listagem, contadores e e-mail (SendGrid API)

Formulário (nome + função) com persistência em SQLite, listagens/contadores
de usuários e funções, e envio de e-mail via **SendGrid (API HTTP, SDK
oficial `sendgrid`)** sempre que um usuário novo é cadastrado.

## 1. Limpar resíduos de semanas anteriores (se houver)

No diretório da aplicação (`~/flasky`):

```bash
rm -rf migrations
rm -f data.sqlite
```

## 2. Trazer o código deste repositório

```bash
chmod 777 change_repo.sh
./change_repo.sh <link-do-repo>
```

## 3. Ambiente virtual e dependências

Se o venv já existir e estiver ativo (prompt mostrando `(venv)`), só instale
as dependências:

```bash
pip install -r requirements/common.txt
```

(Isso inclui o pacote `sendgrid`, usado agora no lugar do Flask-Mail.)

## 4. Criar o `.env`

Na raiz do projeto (mesmo nível do `hello.py`):

```bash
nano .env
```
Conteúdo (sem aspas, sem espaços em volta do `=`):
```
API_KEY=sua_api_key_do_sendgrid
```
Salvar: `Ctrl+O`, `Enter`, `Ctrl+X`.

**Importante:** o remetente fixo no código é `matheus.quadros@aluno.ifsp.edu.br`
— esse endereço precisa estar verificado no SendGrid (Settings → Sender
Authentication → Single Sender Verification), senão o envio é rejeitado.

## 5. Banco de dados

```bash
export FLASK_APP=hello.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## 6. Reload

Aba **Web** → **Reload**.

## 7. Testar o envio de e-mail direto (sem passar pela thread)

```bash
flask shell
>>> send_async_email('Teste')
```
Isso imprime na hora o status code (202 = aceito pelo SendGrid) ou o erro,
se houver. Depois, confira em SendGrid → Activity Feed se o e-mail aparece
como *Delivered*.
