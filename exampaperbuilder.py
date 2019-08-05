from app import create_app, db
from app.models import User, Question, Exam_Boards


app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Question': Question, 'Exam_Boards':Exam_Boards}


#To set up instant run
#if __name__ == '__main__':
#    
#    app.run(debug=True)