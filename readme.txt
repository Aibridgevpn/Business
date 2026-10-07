Инструкция по разворачиванию бота Business
1.	Подключаемся на сервер по ssh

2.	Клонируем проект git clone [адрес ресурса] [имя папки]
Пример git clone https://github.com/Aibridgevpn/Business.git Business

3.	Переключаемся на root пользователя: su жмем enter и вводим пароль

4.	Устанавливаем Python venv для возможности создания виртуального окружения
apt update 
apt install python3.11-venv

5.	Далее необходимо установить шрифты Microsoft так как они используются в боте для кириллицы на штрих кодах. Для этого сначала включаем контриб для возможности загрузки шрифтов
sed -i '/^deb / {/\bcontrib\b/! s/ main/ main contrib/}' /etc/apt/sources.list  

6.	Затем устанавливаем шрифт
apt install ttf-mscorefonts-installer

7.	Выходим из пользователя root:
 	exit или su [имя пользователя]

8.	Переходим в папку с проектом командой :
cd [имя папки]

9.	Создаем виртуальное окружение и активируем его
python3 -m venv venv
source venv/bin/activate

10.	Импортируем библиотеки в виртуальное окружение с помощью файла requirements.txt
pip install -r requirements.txt

11.	Запускаем бота
nohup python3 main.py &python3
