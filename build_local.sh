#mysql -u root
#drop database Cubydb;
#CREATE DATABASE Cubydb default character set utf8mb4 COLLATE = utf8mb4_unicode_ci;
#quit

source activate django
echo "=> source dj venv successfully, rm caches..."
rm -rf Cuby/**/migrations/00*
rm -rf Cuby/**/migrations/__pycache__
echo "=> rm caches successfully, make migs..."
cd Dia
python manage.py makemigrations user
python manage.py makemigrations article
python manage.py makemigrations resource
python manage.py makemigrations mainpage
python manage.py migrate
echo "=> db migrated successfully, run server..."
python manage.py runserver
echo "=> server exited"
