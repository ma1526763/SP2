import datetime
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, redirect, url_for, request, abort, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from sqlalchemy.orm import relationship
from wtforms import StringField, SubmitField, BooleanField, URLField, EmailField, PasswordField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditor, CKEditorField
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, UserMixin, current_user, login_required, logout_user


app = Flask(__name__)
app.app_context().push()
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# CONFIGURE TABLE
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    # This will act like a List of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("blogPost", back_populates="author")

class blogPost(db.Model):
    __tablename__ = "blog_post"
    id = db.Column(db.Integer, primary_key=True)
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, the "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="posts")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
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

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    posts = blogPost.query.all()
    return render_template('index.html', posts=posts, current_user=current_user)

@app.route('/show-post/<int:post_id>', methods=['GET', "POST"])
def show_post(post_id):
    post_to_show = blogPost.query.get(post_id)
    return render_template('post.html', post=post_to_show, current_user=current_user)

@app.route('/edit-post/<int:post_id>', methods=['GET', "POST"])
@admin_only
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
    return render_template('make-post.html', form=form, edit=True, post_id=post_id, current_user=current_user)

@app.route('/new-post', methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = makePostForm()
    if form.validate_on_submit():
        new_post = blogPost(title=request.values['title'], subtitle=request.values['subtitle'],
                            author=request.values['name'], img_url=request.values['img_url'],
                            body=request.values['blog_content'], date=datetime.datetime.now().strftime("%B %d, %Y"))
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('make-post.html', form=form, edit=False, current_user=current_user)

@app.route("/delete\<int:post_id>")
@admin_only
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
        already_user = User.query.filter_by(email=email).first()
        if already_user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        hash_and_salted_password = generate_password_hash(
            request.values['password'],
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(name=name, email=email, password=hash_and_salted_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template("register.html", form=form, current_user=current_user)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=request.values['email']).first()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        if check_password_hash(user.password, request.values['password']):
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html", form=form)

@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)

@app.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)