from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin,LoginManager,login_user, logout_user,login_required

from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from flask_login import LoginManager
from flask_login import current_user
from collections import defaultdict
#from zoneinfo import ZoneInfo
#タイム管理 pytz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class Study(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100))
    content = db.Column(db.String(200))
    hours = db.Column(db.Float)  
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    


    #date = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Tokyo')))
    #date = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Tokyo')))




class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(200))



with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




@app.route('/', methods = ['GET', 'POST'])
@login_required
def index():
    if request.method == "POST":
        subject = request.form.get('subject')
        content = request.form.get('content')
        try:
            hours = float(request.form.get('hours'))
        except ValueError:
            return "数字を入力してください"    

        

        new_study = Study(subject=subject, content=content, hours=hours, user_id=current_user.id)
        db.session.add(new_study)
        db.session.commit()
        return redirect('/')
    else:
        studies = Study.query.filter_by(user_id=current_user.id).all()
        return render_template('index.html', studies=studies)

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        user = User(username=username, password=generate_password_hash(password,method='pbkdf2:sha256'))
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else:
        return render_template('signup.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password,password):
            login_user(user)
            return redirect('/')
    else:
        return render_template('login.html',error="ユーザー名またはパスワードが違います")
    return render_template('login.html',error="ユーザー名またはパスワードが違います")
    

@app.route('/logout')
@login_required #ログイン制限
def logout():
    logout_user()
    return redirect('/login')




@app.route('/<int:id>/update', methods = ['GET', 'POST'])
@login_required
def update(id):
    study = Study.query.filter_by(id=id,user_id=current_user.id).first_or_404()
    
    if request.method == "POST":
        study.subject = request.form.get('subject')
        study.content = request.form.get('content')
        db.session.commit()
        return redirect('/')
    else:
        return render_template('update.html', study=study)

@app.route('/<int:id>/delete', methods = ['GET', 'POST'])
@login_required
def delete(id):
    study = Study.query.filter_by(id=id,user_id=current_user.id).first_or_404()

    db.session.delete(study)
    db.session.commit()
    return redirect('/')

@app.route('/graph')
@login_required
def graph():
    studies = Study.query.filter_by(user_id=current_user.id).all()

     
    hours = [s.hours for s in studies]
    total_hours = sum([s.hours for s in studies])
    daily_hours = defaultdict(float)
    for s in studies:     #Pythonで日付データを文字列に変換してリスト化している処理
         date = s.date.strftime("%Y-%m-%d")
         daily_hours[date] += s.hours


    return render_template('graph.html',hours=hours,total_hours=total_hours,daily_hours=daily_hours )


        
if __name__ == '__main__':
    app.run(debug=True)
