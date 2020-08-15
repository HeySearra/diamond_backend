# mysql -u root -p
# ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '';

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
lg_info "venv \`${dj_name}\` activated, pip install dependencies... (listed in \`req.txt\`)"
pip install -r req.txt


lg_info "dependencies installed, rebuild database..."
sh ./drop.sh


lg_info "ready to build, use \`sh ./build.sh\` to build-and-run"
