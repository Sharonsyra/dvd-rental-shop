from flask import Flask, render_template, session, request, abort, redirect, url_for

import psycopg2
import random
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET')
host = os.getenv('SERVER_HOST')
database = os.getenv('DATABASE_NAME')
user = os.getenv('USER_ROLE')
password = os.getenv('PASSWORD')

try:
    con = psycopg2.connect(host=host, database=database, user=user, password=password)
except Exception as e:
    app.logger.warning("Unable to connect to the database")
else:
    cur = con.cursor()
    app.logger.info("Connected!!")

@app.route('/')
def index():
    if request.method == 'GET':
        results = []
        cur.execute("SELECT count(film_id)\
        FROM public.film WHERE description iLIKE '%croc%' AND description iLIKE '%shark%'; ")
        croc_shark = cur.fetchall()
        results.append(croc_shark)
        cur.execute("""select custor.first_name, custor.last_name
        from (select first_name, last_name
            from public.customer as cust
            union
            select first_name, last_name
            from public.actor as act) custor 
        where custor.first_name = (select first_name from actor where actor_id=8)
        """)
        names = cur.fetchall()
        results.append(names)
        cur.execute("""select cat.name, count(film_cat.film_id)
        from public.film_category as film_cat 
        inner join public.category as cat 
        ON film_cat.category_id = cat.category_id 
        inner join public.film as fil 
        ON film_cat.film_id = fil.film_id 
        group by cat.name having count(*) BETWEEN 55 AND 65 
        order by count(film_cat.film_id)""")
        film_categories = cur.fetchall()
        results.append(film_categories)
        con.commit()
        app.logger.warning("{} results found".format(len(results)))
        return render_template('index.html', results=results)

@app.route('/add_film', methods = ['GET', 'POST'])
def add_film():
    if request.method == 'GET':
        return render_template('films.html')

    elif request.method == 'POST':
        film_title = request.form['film_title']
        film_description = request.form['description']
        release_year = request.form['release_year']
        language = request.form['film_language']
        language_value = cur.execute("select language_id from public.language where name = (%s)", [language])
        film_language = cur.fetchall()
        rental_duration = request.form['rental_duration']
        rental_rate = request.form['rental_rate']
        film_length = request.form['film_length']
        replacement_cost = request.form['replacement_cost']
        rating = request.form['film_rating']
        value = cur.execute("select * from public.mpaa_rating(%s)", (rating))
        film_rating = cur.fetchall()
        
        cur.execute("""INSERT INTO public.film ( 
        title, description ,release_year ,language_id, rental_duration, rental_rate, length,replacement_cost,rating) 
        VALUES 
        (%s, %s, %s, %s ,%s ,%s ,%s ,%s ,%s)""",
        (film_title, film_description, release_year, film_language[0] ,rental_duration ,rental_rate ,film_length ,replacement_cost ,film_rating[0]))
        
        con.commit()

        return redirect(url_for('add_film'))


@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            print(request.form.get('_csrf_token'))
            return render_template('error.html', error = 'CSRF ERROR')

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = random.random()
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token 

if __name__ == '__main__':
    app.run(debug = True)
