from flask import Flask,request,g
import sqlite3
from datetime import date,datetime
from flask_restplus import Api, Resource, fields
from werkzeug.contrib.fixers import ProxyFix
from functools import wraps


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)


authorizations = {
    'apikey':{
        'type' :'apiKey',
        'in' : 'header',
        'name' : 'X-API-KEY'
    }
}
def token_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        token=None

        if 'X-API-KEY' in request.headers:
            token =request.headers['X-API-KEY']
        if not token:
            return {'message':'Token is missing'},401
        if token != 'token':
            return {'message':'Your token is incorrect'},401

        print('Token {}'.format(token))
        return f(*args,**kwargs)
    return decorated



api = Api(app, version='1.0', title='TodoMVC API',
    description='A simple TodoMVC API',authorizations=authorizations,
)

DATABASE = 'iplab.db'
conn = sqlite3.connect(DATABASE)
cursor=conn.cursor()
command1="""create TABLE IF NOT EXISTS toto2(id INTEGER PRIMARY KEY, task TEXT , due_date TEXT, status TEXT)"""
cursor.execute(command1)
conn.close()

ns = api.namespace('todos', description='TODO operations')

todo = api.model('Todo', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details'),
    'due_date':fields.String(required=True,description='last date to finish the task'),
    'status':fields.String(required=True,description='check the task is finished or not')
    
})


def dict_from_row(row):
    return dict(zip(row.keys(), row))


class TodoDAO(object):
    def __init__(self):
        self.counter = 0
        self.todos = []

    def get(self, id):
        todos=self.getall()
        
        for i in todos:
            todo_dic=dict_from_row(i)
            if(todo_dic['id']==id):
                return todo_dic
    
    def getall(self):
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor=conn.cursor()
        sql='''SELECT * FROM toto2'''
        cursor.execute(sql)
        result=cursor.fetchall()
        conn.commit()
        conn.close()
        return result  

    def create(self, data):
        todos=self.getall()
        counter=0
        for i in todos:
            todos=dict_from_row(i)
            counter=counter+1
        todo=data
        todo['id'] = counter + 1
        conn = sqlite3.connect(DATABASE)
        cursor=conn.cursor()
        sql='''INSERT OR IGNORE INTO toto2 VALUES(?,?,?,?)'''
        cursor.execute(sql,(todo['id'],data['task'],todo['due_date'],todo['status']))
        conn.commit()
        conn.close()
        return todo

    def update(self, id, data):
        todo = self.getall()
        for i in todo:
            todos=dict_from_row(i)
            if(todos['id']==id):
                todos['task']=data['task']
                conn = sqlite3.connect(DATABASE)
                cursor=conn.cursor()
                sql='''UPDATE toto2 SET task=? WHERE id=? '''
                cursor.execute(sql,(todos['task'],todos['id']))
                conn.commit()
                conn.close()
        return todos

    def getoverdue(self):
        over_due=[]
        current_date=datetime.today().strftime('%d-%m-%Y')
        todos=self.getall()
        for i in todos:
            updated_todo=dict_from_row(i)
            if(updated_todo['due_date'] > current_date and updated_todo['status'] == "notcompleted"):
                over_due.append(updated_todo)
        return over_due

    def delete(self, id):
        todo = self.get(id)
        conn = sqlite3.connect(DATABASE)
        cursor=conn.cursor()
        sql='''DELETE FROM toto2 WHERE id = ? '''
        cursor.execute(sql,(todo['id'],))
        conn.commit()
        conn.close()
        
    def updatestatus(self, id,status):
        n=0
        todos=self.getall()
        for i in todos:
            todos_new=dict_from_row(i)
            if(todos_new['id']==id):
                todos_new['status']=status
                conn = sqlite3.connect(DATABASE)
                cursor=conn.cursor()
                sql='''UPDATE toto2 SET status = ? WHERE id = ? '''
                cursor.execute(sql,(todos_new['status'],todos_new['id']))
                conn.commit()
                conn.close()
                return todos_new
        
    def getfinished(self):
        n=0
        get_finished=[]
        todos=self.getall()
        for i in todos:
            todos_updates=dict_from_row(i)
            if(todos_updates['status'] == "completed"):
                get_finished.append(todos_updates)
        if(len(get_finished) > 0):
            return get_finished

    def getdue(self,date):
        todos=self.getall()
        get_due=[]
        for i in todos:
            todo=dict_from_row(i)
            if(todo['due_date']==date and todo['status'] == "notcompleted"):
                get_due.append(todo)
        return get_due

DAO = TodoDAO()
DAO.create({'task': 'Build an API','due_date':'20-05-2021','status':'completed'})
DAO.create({'task': 'Build an PAi','due_date':'10-05-2021','status':'completed'})
DAO.create({'task': 'Build an PAi','due_date':'25-05-2021','status':'notcompleted'})



@ns.route('/')
class TodoList(Resource):
    
    '''Shows list of all types of operations on Todos'''
    @ns.doc('list_todos')
    @ns.marshal_list_with(todo)
    def get(self):
        '''List all tasks with all details'''
        return DAO.getall(),201

    @ns.doc('create_todo')
    @ns.doc(security='apikey')
    @token_required
    @ns.expect(todo)
    @ns.marshal_with(todo, code=201)
    def post(self):
        '''Create a new task'''
        return DAO.create(api.payload), 201


@ns.route('/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    '''Can see single Todo item and can delete the item'''
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    def get(self, id):
        '''Select a specific task'''
        return DAO.get(id)

    @ns.doc('delete_todo')
    @ns.response(204, 'Todo deleted')
    def delete(self, id):
        '''Delete a specific task based on the identifier'''
        DAO.delete(id)
        return '', 204

    @ns.expect(todo)
    @ns.marshal_with(todo)
    def put(self, id):
        '''Update a specific task based on the given identifier'''
        return DAO.update(id, api.payload)

@ns.route('/start/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')

class TodoStart(Resource):
    @ns.doc('start_todo')
    @ns.doc(security='apikey')
    @token_required
    @ns.response(201, 'Todo Started')
    def get(self, id):
        '''Update the status of task as notcompleted , given its identifier'''
        return DAO.updatestatus(id,'notcompleted'), 201
    
@ns.route('/finish/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class TodoFinish(Resource):
    @ns.doc('finish_todo')
    @ns.doc(security='apikey')
    @token_required
    @ns.response(201, 'Todo Completed')
    def get(self, id):
        '''Update the status of task as completed , given its identifier'''
        return DAO.updatestatus(id,'completed'), 201

@ns.route('/overdue')
@ns.response(404, 'No Overdue Tasks')
class TodoOverdue(Resource):
    @ns.doc('overdues')
    @ns.response(201, 'Overdue Todos Displayed')
    def get(self):
        '''All the overdue tasks are displayed'''
        return DAO.getoverdue(), 201

@ns.route('/finished')
@ns.response(404, 'No Finished Tasks')
class TodoOverdue(Resource):
    @ns.doc('finished')
    @ns.response(201, 'Finished Todos Displayed')
    def get(self):
        '''Displays all finished tasks'''
        return DAO.getfinished(), 201

@ns.route('/due')
@ns.response(404, 'No Todo due on this date found')
@ns.param('due_date', 'The task due date specified')
class TodoDue(Resource):
    @ns.doc('due')
    @ns.response(201, 'Todos due on the date is Displayed')
    def get(self):
        '''Given a date , it displays all the tasks which are due on that date'''
        date=request.args['due_date']
        return DAO.getdue(date), 201


if __name__ == '__main__':
    app.run(debug=True)
