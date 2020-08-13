if [ "${DJ_CONDA_ENV}" ];then
  dj_name=${DJ_CONDA_ENV}
else
  dj_name="dj"
fi

source activate "${dj_name}"

echo "=> source ${dj_name} venv successfully, rm caches..."
rm -rf Dia/**/migrations
rm -rf Dia/**/migrations/*
rm -rf Dia/**/migrations/00*
rm -rf Dia/**/migrations/__pycache__
echo "=> rm caches successfully, make migs..."
cd Dia || exit

cwd=$(pwd)
for dir in $(find . -name views.py)''
do
  cd "$(dirname "$dir")" || exit
  pack=${PWD##*/}
  cd "${cwd}" || exit
  python manage.py makemigrations "${pack}"
  echo "=> make ""${pack}"
done;
python manage.py migrate
echo "=> db migrated successfully, run server..."

if [ "$1" ];then
  mode="shell"
else
  mode="runserver"
fi

python manage.py "${mode}"

echo "=> server exited"
