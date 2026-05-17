1) Clonar el repositorio

git clone https://github.com/Otm33/Ingenieria_de_software_TuTrueque.git
cd Ingenieria_de_software_TuTrueque

2) Prender el docker


docker compose up --build

3) Aplicar Migraciones


docker compose exec backend python manage.py migrate
