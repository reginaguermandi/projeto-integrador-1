# Biblioteca Solidária - Backend

Este é o repositório do backend do projeto **Biblioteca Solidária**, desenvolvido para gerenciar o sistema de doação de livros de uma biblioteca comunitária.

## Tecnologias Utilizadas

- **Linguagem**: [Python](https://www.python.org/)
- **Framework**: [Django e Django Rest Framework](https://www.django-rest-framework.org/)
- **Banco de Dados**: [SQLite](https://sqlite.org/)
- **Autenticação**: [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/)

## Funcionalidades

- Cadastro de usuários.
- Gerenciamento de livros (inserção, edição, exclusão e listagem).
- Gerenciamento de doações.
- Controle de disponibilidade de livros.
- Autenticação e autorização de usuários.

## Como Executar

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/biblioteca-solidaria-backend.git
```

2. Crie e ative um ambiente virtual:

- Linux/macOS:

  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

- Windows (CMD):

  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Aplique as migrações do banco de dados:

```bash
python manage.py migrate
```

5. Crie um superusuário para acessar o admin do Django:

```bash
python manage.py createsuperuser
```

O terminal vai te pedir algumas informações, como:

**Username**: nome de usuário

**Email address**: e-mail do admin

**Password**: senha (vai pedir pra digitar duas vezes)

Depois disso, o usuário será criado e você poderá acessar o painel administrativo em: http://127.0.0.1:8000/admin

Use o nome de usuário e a senha que você criou.

6. Inicie o servidor de desenvolvimento:

```bash
python manage.py runserver
```

O servidor estará rodando em: http://127.0.0.1:8000
