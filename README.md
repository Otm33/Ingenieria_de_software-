1) Clonar el repositorio

git clone https://github.com/Otm33/Ingenieria_de_software_TuTrueque.git
cd Ingenieria_de_software_TuTrueque

2) instalar docker

https://www.docker.com/


3) Prender el docker


docker compose up --build

4) Aplicar Migraciones

docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
