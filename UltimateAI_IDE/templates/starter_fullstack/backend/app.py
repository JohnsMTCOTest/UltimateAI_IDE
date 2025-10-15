from flask import Flask
from routes.todo_routes import todo_bp
app = Flask(__name__)
app.register_blueprint(todo_bp, url_prefix='/api')
if __name__=='__main__':
    app.run(debug=True)