from flask import (
    Flask,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for
    )
from console_log import ConsoleLog
from hashlib import sha256
import datetime
from mysql.connector import connect, Error
from os import listdir
from os.path import isfile, join
import random
import logging

#console = logging.getLogger("console")
#console.setLevel(logging.DEBUG)

try:
    connection = connect(
        host="localhost",
        user="debian-sys-maint",
        password="08UNyp81HX5R5saN",
        database="epsio",
    )
    cursor = connection.cursor()
except Error as e:
    print(e)


app = Flask(__name__)
app.secret_key = '6dfe97e73e5738c79fc0ffda59362dfe7ad182707f273af5e42b3ce8c67609b6'
app.permanent_session_lifetime = datetime.timedelta(days=14)
#app.wsgi_app = ConsoleLog(app.wsgi_app, console)

@app.route("/")
def root():
    if "user_id" not in session:
        return redirect(url_for("login"))
    else:
        return redirect(url_for("home"))


def check(num):
    if num > 20:
        num = int(str(num)[-1])
    if num == 0 or 5 <= num <= 20:
        return "лет"
    elif num == 1:
        return "год"
    elif 2 <= num <= 4:
        return "года"
    return "лет"


@app.route("/home", methods=["GET", "POST"])
def home():
    if "user_id" in session:
        cursor.execute(f"select * from dogs where user_id='{session['user_id']}'")
        dogs = cursor.fetchall()
        if len(dogs) == 0:
            return render_template("no_dogs.html")
        else:
            cursor.execute(f"select breed_id from dogs where user_id='{session['user_id']}'")
            breeds = cursor.fetchall()
            dogs = ", ".join(str(x[0]) for x in breeds)
            query = f"select * from dogs where breed_id in ({dogs}) and user_id != '{session['user_id']} '"
            cursor.execute(query)
            result = cursor.fetchall()
            if len(result) == 0:
                return render_template("no_pair.html")
            dog = random.choice(result)
            session["dog"] = dog
            cond = to_show(dog)
            count = 0
            while not cond[0]:
                dog = random.choice(result)
                cond = to_show(dog)
                count += 1
                if count >= 50:
                    return render_template("no_pair.html")
            session["dog"] = dog
            if cond:
                age = datetime.datetime.today().year - dog[5].year
                year = check(age)
                path = "/var/www/html/epsio/static/img/doges"
                files = listdir(path)
                for el in files:
                    filename = el.split(".")
                    if str(dog[0]) == filename[0]:
                        filename = el
                        break
                return render_template("home.html", title=f"{dog[2]}, {age} {year}", bio=dog[4], pic=f"static/img/doges/{filename}")
            return render_template("home.html", log=dog)
            #cursor.execute(f"select * from dogs where breed_id in {}")
            #return render_template("home.html")
    else:
        return redirect(url_for("login"))


@app.route("/like")
def like():
    cursor.execute(f"insert into likes (user_id, liked_id, action, dog_id) values ({session['user_id']}, {session['dog'][1]}, 0, {session['dog'][0]})")
    connection.commit()
    return "nothing"


@app.route("/dislike")
def dislike():
    cursor.execute(f"insert into likes (user_id, liked_id, action, dog_id) values ({session['user_id']}, {session['dog'][1]}, 1, {session['dog'][0]})")
    connection.commit()
    return "nothing"


def to_show(dog):
    user_id = dog[1]
    query = f"select action, dog_id from likes where user_id={session['user_id']} and liked_id={user_id}"
    cursor.execute(query)
    res = cursor.fetchall()
    for el in res:
        if el[0] == 1:
            return False, res, dog
    return True, res, dog


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))
    cursor.execute("select * from districts")
    data = []
    for el in cursor:
        data.append(el)
        data = sorted(data, key=lambda x: x[1])
    if request.method == "POST":
        if "login" in request.form:
            login = request.form["login"]
        else:
            return render_template("register.html", districts=data, warn="Заполните все поля")
        if "password" in request.form:
            password = sha256(request.form["password"].encode("utf-8")).hexdigest()
        else:
            return render_template("register.html", districts=data, warn="Заполните все поля")        
        if "phone" in request.form:
            phone = request.form["phone"]
        else:
            return render_template("register.html", districts=data, warn="Заполните все поля")
        if "email" in request.form:
            email = request.form["email"]
        else:
            return render_template("register.html", districts=data, warn="Заполните все поля")
        if "district" in request.form:
            district_id = request.form["district"]
        else:
            return render_template("register.html", districts=data, warn="Заполните все поля")
        cursor.execute(f"select name from users where name='{login}'")
        for el in cursor:
            if el[0] == login:
                return render_template("register.html", districts=data, warn=f"Имя пользователя уже занято")
        cursor.execute(f"insert into users (name, district_id, phone, email, password) values ('{login}', {int(district_id)}, '{phone}', '{email}', '{password}')")
        connection.commit()
        cursor.execute(f"SELECT id FROM users where name='{login}'")
        
        for el in cursor:
            session["user_id"] = el[0]
            return redirect(url_for("home"))
    return render_template("register.html", districts=data)


@app.route("/profile/add", methods=["GET", "POST"])
def add():
    cursor.execute("select * from breeds")
    data = []
    for el in cursor:
        data.append(el)
        data = sorted(data, key=lambda x: x[1])
    if request.method == "POST":
        if "name" in request.form:
            name = request.form["name"]
        else:
            return render_template("add.html", breeds=data, warn="Заполните все поля")
        if "sex" in request.form:
            sex = request.form["sex"]
        else:
            return render_template("add.html", breeds=data, warn="Заполните все поля")
        if "breed" in request.form:
            breed = request.form["breed"]
        else:
            return render_template("add.html", breeds=data, warn="Заполните все поля")
        if "skills" in request.form:
            skills = request.form["skills"]
        else:
            return render_template("add.html", breeds=data, warn="Заполните все поля")
        if request.form["date"] == "" or "date" not in request.form:
            return render_template("add.html", breeds=data, warn="Заполните все поля")
        else:
            date = request.form["date"]
        if "file" in request.files:
            file = request.files['file']
        else: 
            return render_template("add.html", breeds=data, warn="Заполните все поля")
       # return ", ".join(x for x in (name, sex, breed, skills, date))
        cursor.execute(f"select * from dogs where user_id='{session['user_id']}' and name='{name}'")
        if len(cursor.fetchall()) != 0:
            return render_template("add.html", breeds=data, warn="У вас уже есть собака с такой кличкой")
        cursor.execute(f"insert into dogs (user_id, name, breed_id, skills, br_date, sex) values ('{session['user_id']}', '{name}', '{int(breed)}', '{skills}', '{date}', '{sex}')")
        connection.commit()
        cursor.execute(f"select id from dogs where user_id='{session['user_id']}' and name='{name}'")
        for el in cursor:
            doge_id = el[0]
        path = f"/var/www/html/epsio/static/img/doges"
        #os.system(f"sudo mkdir {path}")
        #os.mkdir(path)
        #os.chmod(path, stat.S_IRWXO)
        file.save(f"{path}/{str(doge_id)}.{file.filename.split('.')[-1]}")
        return render_template("added.html")
    return render_template("add.html", breeds=data)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        login = request.form["login"]
        password = request.form["password"]
        #try
        cursor.execute(f"select id, password from users where name='{login}'")
        
        for el in cursor:
            if sha256(password.encode("utf-8")).hexdigest() == el[1]:
                session["user_id"] = el[0]
                return redirect(url_for("home"))
            else:
                return render_template("login.html", warn="Неверное имя пользователя или пароль")
        return render_template("login.html", warn="Пользователь не найден")
    return render_template("login.html")


@app.route("/profile")
def profile():
    query = f"select * from dogs where user_id={session['user_id']}"
    cursor.execute(query)
    data = cursor.fetchall()
    for i in range(len(data)):
        age = datetime.datetime.today().year - data[i][5].year
        year = check(age)
        path = f"static/img/doges/{get_path(data[i])}"
        data[i] = (path, f"{data[i][2]}, {age} {year}", data[i][4])
    return render_template("profile.html", dogs=data)


def get_path(dog):
   path = "/var/www/html/epsio/static/img/doges"
   files = listdir(path)
   for el in files:
       filename = el.split(".")
       if str(dog[0]) == filename[0]:
           filename = el
           break
   return filename


@app.route("/chat")
def chat():  # fuck you, daniil
    """Отдельное спасибо моему напарнику Даниилу,
    ведь ты выполнил каждое взятое на себя обязательство,
    да еще и своевременно сообщал о возникших проблемах
    в ходе твоей работы
    https://github.com/zelcamn 1Love!"""

    query = "select user_id, liked_id, action, dog_id from likes where action=0"
    cursor.execute(query)
    lst = cursor.fetchall()
    result = list(map(lambda x: x[:-1], lst))
    likes = []
    for el in lst:
        if el[2] == 0 and el[0] == session["user_id"]:
            if (el[1], el[0], 0) in result:
                likes.append((el[1], el[3]))
    likes = list(set(likes))
    if len(likes) == 0:
        return render_template("no_likes.html")
    query = f"select * from users where id in ({', '.join(str(x[0]) for x in likes)})"
    cursor.execute(query)
    result = cursor.fetchall()    
    path = "/var/www/html/epsio/static/img/doges/"
    files = listdir(path)
    data = []
    for i in range(len(likes)):
        for el in files:
            filename = el.split(".")
            if str(likes[i][1]) == filename[0]:
                filename = el
                break
        query = f"select name from dogs where id={likes[i][1]}"
        cursor.execute(query)
        res = cursor.fetchall()
        name = res[0][0]
        #return str(result[i])
        phone = result[i][3]
        email = result[i][4]
        info = f"Телефон: {phone}, почта: {email}"
        data.append(("static/img/doges/" + filename, name, info))
    return render_template("chat.html", dogs=data) 

    return str((str(filename), str(name), str(info)))
    

