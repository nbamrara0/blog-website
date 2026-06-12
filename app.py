import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = "your_secret_key_here"


ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'mysecretpassword123')

# Database Setup
# database_url =

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {"sslmode": "require"}
}

db = SQLAlchemy(app)
# Blog Post Database Model
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)


with app.app_context():
    db.create_all()

@app.route('/all-users')
def all_users():

    users = User.query.all()

    result = ""

    for user in users:
        result += f"""
        ID: {user.id}<br>
        Username: {user.username}<br>
        Email: {user.email}<br>
        <hr>
        """

    return result
# ── 1. ROOT ROUTE ──
@app.route('/')
def root():
    return redirect(url_for('login_page'))


# ── 2. USER AUTHENTICATION ROUTES ──
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            session['user'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('home'))

        flash('Invalid email or password', 'error')

    return render_template('login.html')




@app.route('/register', methods=['POST'])
def register():

    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        flash("Email already registered", "error")
        return redirect(url_for('login_page'))

    user = User(
        username=username,
        email=email,
        password=password
    )

    db.session.add(user)
    db.session.commit()

    flash("Account Created Successfully", "success")

    return redirect(url_for('login_page'))


# ── 3. ADMIN PANEL ROUTES ──
@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('new_post'))
        else:
            flash('Invalid ID or Password! Please try again.', 'danger')

    return render_template('adminlogin.html')


@app.route('/admin/new_post', methods=['GET', 'POST'])
def new_post():
    # Security Check
    if not session.get('logged_in'):
        flash('Please login first to access the Admin Panel.', 'warning')
        return redirect(url_for('adminlogin')) # Fixed endpoint name here
    if request.method == 'POST':
        post_title = request.form['title']
        post_category = request.form['category']
        post_content = request.form['content']

        new_blog = Post(title=post_title, category=post_category, content=post_content)
        db.session.add(new_blog)
        db.session.commit()
        flash('Your post was published successfully!', 'success')
        return redirect(url_for('blog'))

    return render_template('admin.html')

@app.route("/post/<int:id>")
def post_detail(id):
    post = Post.query.get_or_404(id)
    return render_template("post_detail.html", post=post)


@app.route('/admin/posts')
def manage_posts():
    if not session.get('logged_in'):
        return redirect(url_for('adminlogin'))

    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('manage_posts.html', posts=posts)



@app.route('/delete_post/<int:id>')
def delete_post(id):
    if not session.get('logged_in'):
        return redirect(url_for('adminlogin'))

    post = Post.query.get_or_404(id)

    db.session.delete(post)
    db.session.commit()

    flash('Post deleted successfully!')
    return redirect(url_for('manage_posts'))



@app.route('/edit_post/<int:id>', methods=['GET', 'POST'])
def edit_post(id):

    if not session.get('logged_in'):
        return redirect(url_for('adminlogin'))

    post = Post.query.get_or_404(id)

    if request.method == 'POST':

        post.title = request.form['title']
        post.category = request.form['category']
        post.content = request.form['content']

        db.session.commit()

        flash('Post updated successfully!')
        return redirect(url_for('manage_posts'))

    return render_template('edit_post.html', post=post)

# ── 4. MAIN PAGES ROUTES ──
@app.route('/home')
def home():
    if 'user' not in session:
        flash('Please log in to continue.', 'error')
        return redirect(url_for('login_page'))
    latest_posts = Post.query\
    .order_by(Post.date_posted.desc())\
    .limit(5)\
    .all()
    return render_template('index.html', posts=latest_posts)


@app.route('/blog')
def blog():
    all_posts = Post.query\
    .order_by(Post.date_posted.desc())\
    .all()
    return render_template('blog_page.html', posts=all_posts)


@app.route("/about")
def about():
    return render_template('about_page.html')

@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        user_message = request.form["message"]

        new_message = messages(
            name=username,
            email=email,
            message=user_message
        )

        db.session.add(new_message)
        db.session.commit()
        print("Saved Successfully")
        return redirect(url_for("contact"))

    return render_template("contact_page.html")

# ── 5. SINGLE COMBINED LOGOUT ROUTE ──
@app.route('/logout')
def logout():
    # Yeh dono sessions (User aur Admin) ko clear kar dega
    session.pop('user', None)
    session.pop('logged_in', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login_page'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)