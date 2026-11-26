
# MedAgenda

Sistema para a gestão de consultas de uma clínica médica, permitindo o cadastro de pacientes, o agendamento de atendimentos e o controle de acesso seguro a prontuários confidenciais com base em perfis de usuários (RBAC).


## Pré-requisitos
- Python 3.13

Ou

- Docker
    
## Rode o projeto

Clone o projeto
```bash
  git clone https://github.com/lorennasilvaa/MedAgenda
```

Entre na pasta do projeto
```bash
  cd MedAgenda
```

Crie um ambiente virtual
```bash
  python -m venv venv
```

Inicie o servidor
- Docker
    ```bash
    docker compose up --build
    ```
    Acesse [http://0.0.0.0:8000/](http://0.0.0.0:8000/) no navegador.

- Local
    ```bash
    python manage.py runserver
    ```
    Acesse [http://127.0.0.1:8000/](http://127.0.0.1:8000/) no navegador.

Execute os comandos

- No docker
    ```bash
    docker compose exec web python manage.py makemigrations
    docker compose exec web python manage.py migrate
    ```

- No local
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

Crie usuários para utilizar o sistema:

_Comandos para Linux, retire o sudo para utilizar no windows_

- Médico
  ```bash
  sudo docker compose exec web python manage.py shell -c "from clinica.models import UsuarioClinica; u, _ = UsuarioClinica.objects.get_or_create(username='med_teste', defaults={'nome': 'Medico', 'cpf': '000.000.000-11', 'cargo': UsuarioClinica.TipoCargo.MEDICO}); u.set_password('123456'); u.save()"
  ```
- Recepcionista
  ```bash
  sudo docker compose exec web python manage.py shell -c "from clinica.models import UsuarioClinica; u, _ = UsuarioClinica.objects.get_or_create(username='rec_teste', defaults={'nome': 'Recepcionista', 'cpf': '000.000.000-10', 'cargo': UsuarioClinica.TipoCargo.RECEPCIONISTA}); u.set_password('123456'); u.save()"
  ```
- Administrador/TI
  ```bash
  sudo docker compose exec web python manage.py shell -c "from clinica.models import UsuarioClinica; u, _ = UsuarioClinica.objects.get_or_create(username='ti_teste', defaults={'nome': 'Admin TI', 'cpf': '000.000.000-00', 'cargo': UsuarioClinica.TipoCargo.TI}); u.set_password('123456'); u.save()"
  ```
## Executando os testes

Em processo...


## Authors

- [@lorennasilvaa](https://www.github.com/lorennasilvaa)
- [@IohanaViterbino](https://www.github.com/IohanaViterbino)

