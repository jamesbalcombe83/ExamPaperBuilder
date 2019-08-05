from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, current_app
from app import db
from flask_login import current_user, login_required
from app.main.forms import EditProfileForm, QuestionForm, ExamBoardForm, CreatePaperForm, EditQuestionForm
from app.models import User, Question, Exam_Boards, Paper, Question_in
from app.main import bp

#Grabs the current date and time when a user visited, happens before a view
@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

#main index page
@bp.route("/", methods=['GET', 'POST'])
@bp.route("/index", methods=['GET', 'POST'])
@login_required #using flask-login to require a login to view
def index():
    return render_template("index.html", title="Home Page")

#handling a user page
@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    #for pagination
    page = request.args.get('page', 1, type=int)

    questions = user.questions.order_by(Question.timestamp.desc()).paginate(
        page, current_app.config['QUESTIONS_PER_PAGE'], False)
    #link for the next set of questions - if there isn't one, its null 
    next_url = url_for('main.user', username=current_user, page=questions.next_num) \
        if questions.has_next else None
    #link for the previous page - if there isn't one, its null    
    prev_url = url_for('main.user', username=current_user, page=questions.prev_num) \
        if questions.has_prev else None

    return render_template('user.html',user=user, questions=questions.items, 
        next_url=next_url, prev_url=prev_url)

@bp.route('/edit_profile/<username>', methods=['GET','POST'])
@login_required
def edit_profile(username):
    form = EditProfileForm(current_user.username)
    #when a POST is sent, submit to check
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.school_name = form.school_name.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.user',username=current_user.username))
    #when the form loads - GET, grab the data
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.school_name.data = current_user.school_name
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

#split create paper and edit paper apart!!
@bp.route('/create_paper', methods=['GET','POST'])
@login_required
def create_paper():
    form = CreatePaperForm()
    if form.validate_on_submit():
        paper = Paper(name=form.name.data, user_id=current_user.id)
        db.session.add(paper)
        db.session.commit()
        flash('The paper was created. Please add questions')
        return redirect(url_for('main.edit_paper', paper_id=paper.id))
    return render_template('create_paper.html', title='Create Paper', form=form)

#view all papers and edit
@bp.route('/view_papers', methods=['GET', 'POST'])
@login_required
def view_papers():
    #for pagination
    page = request.args.get('page', 1, type=int)
    papers = Paper.query.order_by(Paper.date_created.desc()).paginate(
        page, current_app.config['QUESTIONS_PER_PAGE'], False)
    #link for the next set of questions - if there isn't one, its null 
    next_url = url_for('main.view_papers', page=papers.next_num) \
        if papers.has_next else None
    #link for the previous page - if there isn't one, its null    
    prev_url = url_for('main.view_papers', page=papers.prev_num) \
        if papers.has_prev else None

    return render_template('view_papers.html', title='View Papers',
                           papers=papers.items, next_url=next_url,
                           prev_url=prev_url)

@bp.route('/edit_paper', methods=['GET', 'POST'])
@login_required
def edit_paper():
    paper = Paper.query.filter_by(id=request.args.get('paper_id', None)).first()
    title = "Edit Paper - " + paper.name
    #gets all questions that are not in the paper
    questions = paper.not_used()
    #return questions currently in a paper
    used_qs = paper.all_questions()
    #handling the adding of a question
    question = Question.query.filter_by(id=request.args.get('question_id',None)).first()
    
    if question is not None:
        if question in questions:
            paper.add(question)
            flash('The question was added.')
        else:
            paper.delete(question)  
            flash('The question was removed.')

        return redirect(url_for('main.edit_paper', paper_id=paper.id))
    return render_template('edit_paper.html', title=title, paper=paper, 
        questions=questions, used_qs=used_qs
    )

#view all questions - uses the index page but with a different view
@bp.route("/view_questions", methods=['GET', 'POST'])
@login_required
def view_questions():
    #for pagination
    page = request.args.get('page', 1, type=int)
    questions = Question.query.order_by(Question.timestamp.desc()).paginate(
        page, current_app.config['QUESTIONS_PER_PAGE'], False)
    #link for the next set of questions - if there isn't one, its null 
    next_url = url_for('main.view_questions', page=questions.next_num) \
        if questions.has_next else None
    #link for the previous page - if there isn't one, its null    
    prev_url = url_for('main.view_questions', page=questions.prev_num) \
        if questions.has_prev else None

    return render_template('view_questions.html', title='View Questions',
                           questions=questions.items, next_url=next_url,
                           prev_url=prev_url)

#add question
@bp.route("/add_question", methods=['GET', 'POST'])
@login_required #using flask-login to require a login to view
def add_question():
    form = QuestionForm()
    #get all existing examboards from the exam_boards table
    form.exam_board.choices = [(eb.id, eb.name) for eb in Exam_Boards.query.all()]
    if form.validate_on_submit():
        question = Question(body=form.body.data, 
                            author=current_user, 
                            exam_board=form.exam_board.data, 
                            exam_year=form.exam_year.data,
                            exam_session=form.exam_session.data,
                            marks=form.marks.data, 
                            answer=form.answer.data
                            )
        db.session.add(question)
        db.session.commit()
        flash("Question has been added",'info')
        return redirect(url_for('main.index'))

    return render_template("add_question.html", title="Add Question", form=form)

#Editting questions
@bp.route("/edit_question/<question_id>", methods=['GET','POST'])
@login_required
def edit_question(question_id):
    question = Question.query.filter_by(id=question_id).first_or_404()
    form = EditQuestionForm()
    form.exam_board.choices = [(eb.id, eb.name) for eb in Exam_Boards.query.all()]

    #when a POST is sent, submit to check
    if form.validate_on_submit():
        question.body = form.body.data
        question.exam_board=form.exam_board.data
        question.exam_year=form.exam_year.data
        question.exam_session=form.exam_session.data
        question.marks=form.marks.data
        question.answer=form.answer.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.view_questions'))
    #when the form loads - GET, grab the data
    elif request.method == 'GET':
        form.body.data = question.body 
        form.exam_board.data = question.exam_board
        form.exam_year.data = question.exam_year
        form.exam_session.data = question.exam_session
        form.marks.data = question.marks
        form.answer.data = question.answer
    return render_template('edit_question.html', title='Edit Question',
                           form=form)


#add examboard
@bp.route("/add_exam_board", methods=['GET', 'POST'])
@login_required #using flask-login to require a login to view
def add_exam_board():
    form = ExamBoardForm()
    if form.validate_on_submit():
        exam_board = Exam_Boards(name=form.name.data)
        db.session.add(exam_board)
        db.session.commit()
        flash("Exam Board has been added")
        return redirect(url_for('main.add_question'))
    
    return render_template("add_exam_board.html", title="Add Exam Board", form=form)