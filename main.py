import datetime
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, URLField, EmailField, PasswordField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditor, CKEditorField
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, UserMixin

# import requests
# posts = requests.get('https://api.npoint.io/82975389c85afb34e389').json()

app = Flask(__name__)
app.app_context().push()
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///me.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# CONFIGURE TABLE
class blogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)


db.create_all()

# for post in posts:
#     new_post = MY_POST(body=post['body'], title=post['title'], subtitle=post['subtitle'])
#     db.session.add(new_post)
#     db.session.commit()

class makePostForm(FlaskForm):
    title = StringField('Blog Post Title', validators=[DataRequired()])
    subtitle = StringField('Subtitle', validators=[DataRequired()])
    name = StringField('Your Name', validators=[DataRequired()])
    img_url = URLField('Blog Image Url', validators=[DataRequired()])
    blog_content = CKEditorField('Blog Content', validators=[DataRequired()])
    accept_tos = BooleanField('I accept the TOS', validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField("Login")

@app.route('/')
def home():
    posts = blogPost.query.all()
    print(posts)
    return render_template('index.html', posts=posts)

@app.route('/show-post/<int:post_id>', methods=['GET', "POST"])
def show_post(post_id):
    post_to_show = blogPost.query.get(post_id)
    return render_template('post.html', post=post_to_show)

@app.route('/edit-post/<int:post_id>', methods=['GET', "POST"])
def edit_post(post_id):
    post_to_edit = blogPost.query.get(post_id)
    form = makePostForm(
        title=post_to_edit.title,
        subtitle=post_to_edit.subtitle,
        name=post_to_edit.author,
        img_url=post_to_edit.img_url,
        blog_content=post_to_edit.body
    )
    if request.method == "POST":
        post_to_edit.title = request.values['title']
        post_to_edit.subtitle = request.values['subtitle']
        post_to_edit.author = request.values['name']
        post_to_edit.img_url = request.values['img_url']
        post_to_edit.body = request.values['blog_content']
        db.session.commit()
        return redirect(url_for('show_post', post_id=post_id))
    print("OUTSIDE", post_id)
    return render_template('make-post.html', form=form, edit=True, post_id=post_id)

@app.route('/new-post', methods=["GET", "POST"])
def add_new_post():
    form = makePostForm()
    if form.validate_on_submit():
        new_post = blogPost(title=request.values['title'], subtitle=request.values['subtitle'],
                            author=request.values['name'], img_url=request.values['img_url'],
                            body=request.values['blog_content'], date=datetime.datetime.now().strftime("%B %d, %Y"))
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('make-post.html', form=form, edit=False)

@app.route("/delete\<int:post_id>")
def delete_post(post_id):
    post_to_delete = blogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = request.values['name']
        email = request.values['email']
        hash_and_salted_password = generate_password_hash(
            request.values['password'],
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(name=name, email=email, password=hash_and_salted_password)
        db.session.add(new_user)
        db.session.commit()
        # login_user(new_user)
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=request.values['email']).first()
        if check_password_hash(user.password, request.values['password']):
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html", form=form)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)