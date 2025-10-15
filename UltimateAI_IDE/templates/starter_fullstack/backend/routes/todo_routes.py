from flask import Blueprint,jsonify,request
todo_bp = Blueprint('todo_bp',__name__)
todos=[]
@todo_bp.route('/todos',methods=['GET'])
def get_todos():
    return jsonify(todos)
@todo_bp.route('/todos',methods=['POST'])
def add_todo():
    data=request.get_json()
    todos.append(data.get('task',''))
    return jsonify({'success':True,'todos':todos})