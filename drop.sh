# mysql -u root -p
# ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '';

rm -rf Dia/**/migrations
rm -rf Dia/**/migrations/*
rm -rf Dia/**/migrations/00*
rm -rf Dia/**/migrations/__pycache__

function mys_call() {
  l="$1"
  mysql -h"localhost"  -P"3306"  -u"root" -e "${l}" --default-character-set=UTF8
}

db_name="Diadb"
mys_call "drop database ${db_name};" >/dev/null 2>&1
mys_call "CREATE DATABASE ${db_name} default character set utf8mb4 COLLATE = utf8mb4_unicode_ci;"

