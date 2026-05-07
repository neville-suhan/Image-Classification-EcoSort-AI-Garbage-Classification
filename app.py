from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from tensorflow.keras.models import load_model
import os

from predict_utils import predict_image

# -------------------- APP CONFIG --------------------
app = Flask(__name__)

app.config['SECRET_KEY'] = 'garbage'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# -------------------- INIT --------------------
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'login'  # 🔥 Force login first

# -------------------- MODEL LOAD --------------------
MODEL_PATH = "models/mobilenetv2(89% acc).h5"
model = load_model(MODEL_PATH)

# 13 CLASSES
CLASS_NAMES = [
    'battery', 'biological', 'brown-glass', 'cardboard',
    'clothes', 'green-glass', 'metal', 'organic',
    'paper', 'plastic', 'shoes', 'trash', 'white-glass'
]

# -------------------- USER MODEL --------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# -------------------- LOAD USER --------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------- ROUTES --------------------



CLASS_INFO = {
    "battery": {
        "emoji": "🔋",
        "disposal": "• Never throw in regular trash\n• Store used batteries in a dry container\n• Tape terminals to avoid short-circuits\n• Drop at authorized e-waste centers\n• Keep away from children and heat",
        "recycle": "• Use rechargeable batteries\n• Return to electronics stores for recycling\n• Repurpose in low-drain devices (if still usable)\n• Participate in local e-waste drives"
    },

    "biological": {
        "emoji": "🌿",
        "disposal": "• Separate from plastic waste\n• Put in compost bin\n• Avoid cooked/oily food in compost\n• Use closed bins to prevent odor\n• Can be sent for biogas processing",
        "recycle": "• Make compost for plants\n• Use for home gardening\n• Create natural fertilizers\n• Convert into bio-enzymes for cleaning"
    },

    "brown-glass": {
        "emoji": "🍺",
        "disposal": "• Rinse bottles before disposal\n• Separate by color\n• Remove caps and labels\n• Do not break manually\n• Place in glass recycling bins",
        "recycle": "• Reuse as storage bottles\n• DIY lamps or decor\n• Use as planters\n• Make candle holders"
    },

    "cardboard": {
        "emoji": "📦",
        "disposal": "• Flatten boxes to save space\n• Keep dry and clean\n• Remove plastic tape & staples\n• Avoid greasy cardboard (not recyclable)",
        "recycle": "• Use for storage boxes\n• DIY organizers\n• Kids craft projects\n• Compost small pieces (if clean)"
    },

    "clothes": {
        "emoji": "👕",
        "disposal": "• Donate wearable clothes\n• Send damaged ones to textile recycling\n• Avoid throwing in landfill\n• Separate by fabric type if possible",
        "recycle": "• Convert into cleaning cloths\n• DIY bags or tote bags\n• Cushion covers or quilts\n• Upcycle into fashion items"
    },

    "green-glass": {
        "emoji": "🟢",
        "disposal": "• Rinse and clean properly\n• Separate from other glass types\n• Remove lids and caps\n• Dispose in glass bins",
        "recycle": "• Garden decorations\n• Bottle art or painting\n• DIY lighting lamps\n• Use as water storage containers"
    },

    "metal": {
        "emoji": "🥫",
        "disposal": "• Rinse cans before disposal\n• Crush to save space\n• Remove food residue\n• Separate aluminum and steel if possible",
        "recycle": "• Sell as scrap metal\n• DIY pen holders\n• Make small containers\n• Use in creative craft projects"
    },

    "organic": {
        "emoji": "🍂",
        "disposal": "• Compost at home\n• Use green waste bins\n• Avoid mixing plastics\n• Chop large waste for faster composting",
        "recycle": "• Create compost fertilizer\n• Use in gardening\n• Make bio-enzymes\n• Feed animals (safe food scraps only)"
    },

    "paper": {
        "emoji": "📄",
        "disposal": "• Keep dry and clean\n• Avoid oily or wet paper\n• Remove plastic coatings\n• Stack neatly for recycling",
        "recycle": "• Make handmade paper\n• Use for notes/drafts\n• Origami crafts\n• Reuse as packaging material"
    },

    "plastic": {
        "emoji": "🧴",
        "disposal": "• Check recycling code (1–7)\n• Wash before disposal\n• Avoid burning plastic\n• Separate soft and hard plastics",
        "recycle": "• Bottle planters\n• DIY organizers\n• Eco-bricks for construction\n• Reuse containers for storage"
    },

    "shoes": {
        "emoji": "👟",
        "disposal": "• Donate if in good condition\n• Send to footwear recycling units\n• Avoid landfill disposal\n• Clean before donating",
        "recycle": "• Use as garden pots\n• DIY storage holders\n• Creative decor items\n• Rubber reuse projects"
    },

    "trash": {
        "emoji": "🗑️",
        "disposal": "• Dispose in landfill bins\n• Do not mix recyclables\n• Use sealed bags\n• Reduce waste generation daily",
        "recycle": "• Try switching to reusable products\n• Reduce single-use items\n• Segregate properly to minimize trash\n• Follow zero-waste practices"
    },

    "white-glass": {
        "emoji": "🫙",
        "disposal": "• Clean thoroughly before disposal\n• Separate by color\n• Remove lids and labels\n• Place in recycling bins",
        "recycle": "• Use as storage jars\n• Candle holders\n• Decorative jars\n• Kitchen containers"
    }
}

# 🔥 FIRST PAGE → LOGIN ONLY
@app.route('/')
def index():
    return redirect(url_for('login'))

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password!", "danger")

    return render_template('login.html')


# SIGNUP
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
                flash("Passwords do not match!", "danger")
                return redirect(url_for('register'))


        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists!", "warning")
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)

        new_user = User(name=name, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# HOME
@app.route('/home')
@login_required
def home():
    return render_template('home.html')


# DASHBOARD (if used)
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


# -------------------- PREDICT --------------------
@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():

    if request.method == 'POST':

        if 'image' not in request.files:
            flash("No file uploaded!", "danger")
            return redirect(request.url)

        file = request.files['image']

        if file.filename == '':
            flash("No file selected!", "warning")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # create folder if not exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        file.save(filepath)

        # 🔥 PREDICT
        predicted_class, confidence = predict_image(model, filepath, CLASS_NAMES)
        
        
        # normalize (recommended)
        predicted_class = predicted_class.lower()
        
        
        # get tips
        info = CLASS_INFO.get(predicted_class, {})
        emoji = info.get("emoji", "🗑️")
        disposal_tip = info.get("disposal", "No disposal info available")
        recycle_tip = info.get("recycle", "No recycle info available")

        return render_template(
            'predict.html',
            prediction=predicted_class,
            confidence=round(confidence * 100, 2),
            image_path=filepath,
            disposal_tip=disposal_tip,
            recycle_tip=recycle_tip,
            emoji=emoji
        )

    return render_template('predict.html')


# LOGOUT
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))


# -------------------- RUN --------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # auto creates users.db in instance

    app.run(debug=True, port=3007)