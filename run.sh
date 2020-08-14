function lg_info {
    dt=$(date +"[%m-%d %H:%M:%S]")
    echo "=> ${dt} $1"
}


if [ "${DJ_CONDA_ENV}" ]
then
  dj_name=${DJ_CONDA_ENV}
else
  dj_name="dj"
fi
source activate "${dj_name}"


django_proj_root="Dia"
lg_info "venv ${dj_name} activated, rm caches..."
rm -rf "${django_proj_root}/**/migrations"
rm -rf "${django_proj_root}/**/migrations/*"
rm -rf "${django_proj_root}/**/migrations/00*"
rm -rf "${django_proj_root}/**/migrations/__pycache__"


cd "${django_proj_root}" || exit
cwd=$(pwd)
lg_dir="logging"
lg_file="${lg_dir}/run.sh.log"
lg_info "caches removed, make migs... (outputs are redirected to ${lg_file})"
for dir in $(find . -name views.py)''
do
  cd "$(dirname "$dir")" || exit
  pack=${PWD##*/}
  cd "${cwd}" || exit
  python manage.py makemigrations "${pack}"
  lg_info "make migs of ${pack}"
done;
python manage.py migrate


lg_info "db migrated, check lg_infos..."
if [ ! -d "${lg_dir}" ]
then
  lg_info "mk log dir: ${lg_dir}"
  mkdir "${lg_dir}"
fi
lg_file="${lg_dir}/console.log"

if [ ! -f "${lg_file}" ]
then
  lg_info "create log file: ${lg_file}"
  touch "${lg_file}"
fi
lg_file="${lg_dir}/error.log"

if [ ! -f "${lg_file}" ]
then
  lg_info "create log file: ${lg_file}"
  touch "${lg_file}"
fi


lg_info "lg_infos checked, run server..."
if [ "$1" ]
then
  mode="shell"
else
  mode="runserver"
fi
python manage.py "${mode}"


lg_info "server exited"
