from flask import Flask, render_template
from models import db
from routes.auth_routes import auth_bp
import os

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///edusync.db'
app.config['SECRET_KEY'] = 'edusync_secure_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db.init_app(app)

# Register the Authentication Blueprint
app.register_blueprint(auth_bp)

@app.route('/')
def home():
    """Renders the professional home page."""
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        # Creates the database and tables if they don't exist
        db.create_all()
    
    # host='0.0.0.0' allows access over your local Wi-Fi network
    app.run(host='0.0.0.0', port=5000, debug=True)