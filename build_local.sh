#mysql -u root
#drop database Cubydb;
#CREATE DATABASE Cubydb default character set utf8mb4 COLLATE = utf8mb4_unicode_ci;
#quit

if [ "${DJ_CONDA_ENV}" ];then
  dj_name=${DJ_CONDA_ENV}
else
  dj_name="dj"
fi

source activate "${dj_name}"

echo "=> source ${dj_name} venv successfully, rm caches..."
rm -rf Cuby/**/migrations/00*
rm -rf Cuby/**/migrations/__pycache__
echo "=> rm caches successfully, make migs..."
cd Dia || exit
python manage.py makemigrations user
python manage.py makemigrations article
python manage.py makemigrations resource
python manage.py makemigrations mainpage
python manage.py migrate
echo "=> db migrated successfully, run server..."

if [ "$1" ];then
  mode="shell"
else
  mode="runserver"
fi

python manage.py "${mode}"

echo "=> server exited"
