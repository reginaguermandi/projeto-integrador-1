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

### **Fluxo Simples de Uso**

1. **Navegação de Livros (Acesso Livre)**
   - Qualquer usuário pode acessar o site, navegar e visualizar o catálogo.
2. **Cadastro e Login (Usuários Logados)**
   - Para solicitar um livro, o usuário deve se cadastrar com nome, e-mail, senha, data de nascimento e endereço básico.
3. **Solicitação de Livro (Usuários Logados)**
   - Após login, o usuário pode cadastrar livros para doar ou solicitar a doação de um livro disponível.
4. **Entrega e Finalização**
   - O sistema registra o pedido como pendente, o doador tem a opção de aceitar ou negar.
   - Caso aceite, o livro fica aguardando retirada no local informado pelo doador.
   - O status da retirada é atualizado pelo usuário solicitante após a retirada.

## **Rotas**

### **Login**

**POST /api/login/**

Corpo da requisição:

```json
{
	"email": "usuario@email.com",
	"password": "senhasecreta"
}
```

Resposta (200 OK):

```json
{
	"token": "fd345abc123..."
}
```

Resposta Falha(401 Unauthorized):

```json
{
	"detail": "No active account found with the given credentials"
}
```

### Usuários

**POST /api/users/**

Corpo da requisição:

```json
{
	"name": "Meu Nome",
	"email": "meunome@mail.com",
	"password": "123456",
	"birth_date": "1988-04-13",
	"phone": "11999999999",
	"street": "Nome da Rua",
	"number": "456",
	"city": "Cidade",
	"zip": "01001005"
}
```

Resposta (201 created):

```json
{
	"id": 1,
	"name": "Meu Nome",
	"email": "meunome@mail.com",
	"birth_date": "1988-04-13",
	"phone": "11999999999",
	"address": {
		"street": "Nome da Rua",
		"number": "456",
		"city": "Cidade",
		"zip": "01001005"
	}
}
```

Resposta (400 Bad Request):

```json
{
	"name": ["This field may not be blank."],
	"email": ["user with this email already exists."],
	"password": ["A senha deve ter pelo menos 6 caracteres."],
	"birth_date": ["O usuário precisa ter pelo menos 18 anos."],
	"phone": [
		"O número de telefone deve conter entre 10 a 11 dígitos (somente números)."
	],
	"zip": ["O campo cep deve conter exatamente 8 dígitos numéricos."]
}
```

**PATCH /api/users/{id}**

Corpo da requisição: inserir apenas os campos que quer editar

```json
{
	"name": "Meu Novo Nome"
}
```

Resposta (200 OK):

```json
{
	"id": 1,
	"name": "Meu Novo Nome",
	"email": "meunome@mail.com",
	"birth_date": "1988-04-13",
	"phone": "11999999999",
	"address": {
		"street": "Nome da Rua",
		"number": "456",
		"city": "Cidade",
		"zip": "01001005"
	}
}
```

Resposta (400 Bad Request): exemplo de email incorreto

```json
{
	"email": ["Enter a valid email address."]
}
```

**DELETE /api/users/{id}**

Resposta (204 No Content):
