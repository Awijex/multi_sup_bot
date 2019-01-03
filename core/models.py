from flask_sqlalchemy import SQLAlchemy
import os


def create_database(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.curdir), 'database.sqlite')
    db = SQLAlchemy(app)

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.String(10))
        state = db.Column(db.String(50))

        def __init__(self, user_id, state):
            self.user_id = user_id
            self.state = state

        def __repr__(self):
            return self.user_id + ' ' + self.state

    if not os.path.exists('database.sqlite'):
        db.create_all()

    return db, User
