from flask import (
    Flask,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from hashlib import sha256
from datetime import timedelta
from mysql.connector import connect, Error
import os

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
app.permanent_session_lifetime = timedelta(days=14)


@app.route("/")
def root():
    if "user_id" not in session:
        return redirect(url_for("login"))
    else:
        return redirect(url_for("home"))


@app.route("/home")
def home():
    if "user_id" in session:
        cursor.execute(f"select * from dogs where user_id='{session['user_id']}'")
        dogs = cursor.fetchall()
        if len(dogs) == 0:
            return render_template("no_dogs.html")
        else:
            cursor.execute(f"select breed_id from dogs where user_id='{session['user_id']}'")
            breeds = cursor.fetchall()
            query = f"select * from dogs where breed_id in ({', '.join(str(x[0]) for x in breeds)}) and user_id != '{session['user_id']}'"
            cursor.execute(query)
            result = cursor.fetchall()
            return render_template("home.html")
            #cursor.execute(f"select * from dogs where breed_id in {}")
            #return render_template("home.html")
    else:
        return redirect(url_for("login"))


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

