1) Clonar el repositorio

git clone https://github.com/Otm33/Ingenieria_de_software_TuTrueque.git
cd Ingenieria_de_software_TuTrueque

2) instalar docker

https://www.docker.com/


3) Prender el docker


docker compose up --build

4) Aplicar Migraciones (solo la primera vez)

docker compose exec backend python manage.py makemigrations


docker compose exec backend python manage.py migrate

5) Abrir Puertos

Front-end
http://localhost:5173/

Back-end 
http://localhost:8000/api/comunidad/miembros/importar/

6) Ejecutar y Probar

docker-compose exec backend bash

#Ver todos los registros


python manage.py shell -c "from comunidad.models import MiembroComunidad; print(MiembroComunidad.objects.all())"

#Contar cuántos miembros hay guardados


python manage.py shell -c "from comunidad.models import MiembroComunidad; print(MiembroComunidad.objects.count())"

#Buscar un miembro específico por correo



python manage.py shell -c "from comunidad.models import MiembroComunidad; print(MiembroComunidad.objects.filter(correo="juan.perez@example.com"))"






