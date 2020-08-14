rm -rf Dia/**/migrations
rm -rf Dia/**/migrations/*
rm -rf Dia/**/migrations/00*
rm -rf Dia/**/migrations/__pycache__

# mysql -u root -p
# [input your password]
# ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '';


function mys_call() {
  l="$1"
  mysql -h"localhost"  -P"3306"  -u"root" -e "${l}" --default-character-set=UTF8
}

db_name="Diadb"
mys_call "drop database ${db_name};"
mys_call "CREATE DATABASE ${db_name} default character set utf8mb4 COLLATE = utf8mb4_unicode_ci;"
