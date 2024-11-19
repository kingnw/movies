# app/_init_.py

from flask import Flask
from .extensions import db
from .routes import main as main_blueprint  # Assuming you have a blueprint named 'main'

def create_app(config_class='config.DevelopmentConfig'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(main_blueprint)

    return app