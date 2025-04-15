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

# **Rotas**

## Catálogo

### **Listar Catalogo:** `GET /api/books/catalog/` (Sem Proteção)

Corpo da Resposta (200 OK):

```json
[
	{
		"id": 1,
		"title": "Livro AAA",
		"author": "Algum Autor",
		"description": "Descrição do livro.",
		"category": "fantasy",
		"classification": "18_and_up",
		"pickup_point": {
			"id": 1,
			"name": "Padaria do Zé",
			"street": "Nome da Rua",
			"number": "23-12",
			"city": "Cidade",
			"state": "UF",
			"zip": "17015172"
		},
		"status": "available",
		"user": "renata",
		"book_request": null
	},
	{
		"id": 2,
		"title": "Livro BBB",
		"author": "Algum Outro Autor",
		"description": "Outra descrição do livro.",
		"category": "fantasy",
		"classification": "18_and_up",
		"pickup_point": {
			"id": 1,
			"name": "Padaria do Zé",
			"street": "Nome da Rua",
			"number": "23-12",
			"city": "Cidade",
			"state": "UF",
			"zip": "17015172"
		},
		"status": "available",
		"user": "renata",
		"book_request": null
	}
]
```

## **Login**

### **Logar com Usuário:** `POST /api/login/`(Sem Proteção)

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

## Usuários

### **Criar Usuário:** `POST /api/users/` (Sem Proteção)

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

### **Editar Usuário:** `PATCH /api/users/{id}/` (Protegido)

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

### **Deletar Usuário Sem Solicitação Aberta:** `DELETE /api/users/{id}/` (Protegido)

- Corpo da Resposta (204 No Content): Sem conteúdo

### **Detelar Usuário Com Solicitação Aberta:** `DELETE /api/users/{id}/` (Protegido)

Corpo da Resposta (400 Bad Request):

```json
{
	"detail": "Você possui solicitações de livros em aberto. Deseja continuar e cancelar essas solicitações?",
	"open_requests_as_requester": [],
	"open_requests_as_donor": [
		{
			"id": "30",
			"book_title": "Livro AAAA",
			"requester": "lurdes"
		}
	]
}
```

### **Confirmar Exclusão:** `DELETE /api/users/{id}/?confirm=true` (Protegido)

Corpo da Resposta (201 No Content)

## Meus Livros

### **Criar Livro:** `POST /api/my-books/` (Protegido)

Corpo da Requisição:

```json
{
	"title": "Livro AAA",
	"author": "Algum Autor",
	"description": "Descrição do livro.",
	"category": "fantasy",
	"classification": "18_and_up",
	"pickup_point_id": 1
}
```

Corpo da Resposta (201 Created):

```json
{
	"id": 1,
	"title": "Livro AAA",
	"author": "Algum Autor",
	"description": "Descrição do livro.",
	"category": "fantasy",
	"classification": "18_and_up",
	"pickup_point": {
		"id": 1,
		"name": "Padaria do Zé",
		"street": "Nome da Rua",
		"number": "23-12",
		"city": "Cidade",
		"state": "SP",
		"zip": "17015172"
	},
	"status": "available",
	"user": "renata",
	"book_request": null
}
```

##Listar Meus Livros:\*\* `GET /api/my-books/`

```json
[
	{
		"id": 17,
		"title": "Livro AAA",
		"author": "Algum Autor",
		"description": "Outra descrição do livro.",
		"category": "fantasy",
		"classification": "18_and_up",
		"pickup_point": {
			"id": 1,
			"name": "Padaria do Zé",
			"street": "Rua das Camelias",
			"number": "23-12",
			"city": "Bauru",
			"state": "SP",
			"zip": "17015172"
		},
		"status": "requested",
		"user": "lurdes",
		"book_request": {
			"id": 31,
			"requester_name": "carlos",
			"status": "pending"
		}
	},
	{
		"id": 18,
		"title": "Livro BBB",
		"author": "Algum Autor",
		"description": "Outra descrição do livro.",
		"category": "fantasy",
		"classification": "18_and_up",
		"pickup_point": {
			"id": 1,
			"name": "Padaria do Zé",
			"street": "Rua das Camelias",
			"number": "23-12",
			"city": "Bauru",
			"state": "SP",
			"zip": "17015172"
		},
		"status": "available",
		"user": "lurdes",
		"book_request": null
	}
]
```

### **Editar Livro:** `PATCH /api/my-books/{id}/` (Protegido)

Corpo da Requisição: campo que quer atualizar

```json
{
	"author": "Maria E Algumas Coisa"
}
```

Corpo da Resposta (200 OK):

```json
{
	"id": 1,
	"title": "Livro AAA",
	"author": "Maria E Algumas Coisa",
	"description": "Descrição do livro.",
	"category": "fantasy",
	"classification": "18_and_up",
	"pickup_point": {
		"id": 1,
		"name": "Padaria do Zé",
		"street": "Nome da Rua",
		"number": "23-12",
		"city": "Cidade",
		"state": "UF",
		"zip": "17015172"
	},
	"status": "available",
	"user": "renata",
	"book_request": null
}
```

### **Deletar Livro:** `DELETE /api/my-books/{id}/` (Protegido)

- Corpo da Resposta (204 No Content): Sem conteúdo

## Solicitar Doação

### **Solicitar uma doação:** `POST /api/books_requests/` (Protegido)

Corpo da Requisição:

```json
{
	"book_id": 1
}
```

Corpo da Resposta (201 Created):

```json
{
	"id": 1,
	"book": {
		"id": 1,
		"title": "Livro AAA",
		"author": "Algum Autor",
		"donated_by": {
			"id": 1,
			"name": "renata",
			"email": "renata@mail.com"
		}
	},
	"requester_name": "nicolas",
	"pickup_point": {
		"id": 1,
		"name": "Padaria do Zé",
		"street": "Nome da Rua",
		"number": "23-12",
		"city": "Cidade",
		"state": "UF",
		"zip": "17015172"
	},
	"status": "pending"
}
```

### **Listar Solicitações Realizadas:** `GET /api/books_requests/` (Protegido)

Corpo da Resposta (200 OK):

```json
	{
		"id": 1,
		"book": {
			"id": 1,
			"title": "Livro AAA",
			"author": "Algum Autor",
			"donated_by": {
				"id": 2,
				"name": "nicolas",
				"email": "nicolas@mail.com"
			}
		},
		"requester_name": "renata",
		"pickup_point": {
			"id": 1,
			"name": "Padaria do Zé",
			"street": "Rua das Camelias",
			"number": "23-12",
			"city": "Bauru",
			"state": "SP",
			"zip": "17015172"
		},
		"status": "awaiting_pickup"
	}
]
```

### **Atualizar Status da Solicitação:** `PATCH /api/books_requests/{id}/confirm-pickup/` (Protegido)

Corpo da Resposta (200 OK):

```json
{
	"detail": "Retirada confirmada com sucesso. O livro foi marcado como entregue."
}
```

## Solicitações Recebidas

### **Listar solicitações recebidas**: `GET /api/donor-requests/` (Protegido)

```json
{
	"id": 1,
	"book": {
		"id": 1,
		"title": "Livro AAA",
		"author": "Algum Autor",
		"donated_by": {
			"id": 1,
			"name": "renata",
			"email": "renata@mail.com"
		}
	},
	"requester_name": "nicolas",
	"pickup_point": {
		"id": 1,
		"name": "Padaria do Zé",
		"street": "Nome da Rua",
		"number": "23-12",
		"city": "Cidade",
		"state": "UF",
		"zip": "17015172"
	},
	"status": "pending"
}
```

### **Aceitar solicitação recebedida:** `PATCH /api/donor-requests/{id}/approve/` (Protegido)

```json
{
	"detail": "Solicitação aprovada com sucesso. O livro está aguardando retirada."
}
```

### **Negar solicitação recebedida:** `PATCH /api/donor-requests/{id}/deny/` (Protegido)

```json
{
	"detail": "Solicitação negada com sucesso. O livro está disponível no catálogo."
}
```

## Ponto de Coleta

### **Listar Pontos de Coleta:** `GET /api/pickup-points/` (Sem Proteção)

Corpo da Resposta (200 OK):

```json
[
	{
		"id": 1,
		"name": "Padaria do Zé",
		"street": "Nome da Rua",
		"number": "23-12",
		"city": "Cidade",
		"zip": "17015172"
	},
	{
		"id": 2,
		"name": "Sebo da Maria",
		"street": "Nome de Outra Rua",
		"number": "23-13",
		"city": "Cidade",
		"zip": "06600605"
	}
]
```
