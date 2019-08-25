from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
     current_app, jsonify
from app import db
from flask_login import current_user, login_required
from app.main.forms import EditProfileForm, QuestionForm, ExamBoardForm,\
        CreatePaperForm, ExamLevelForm
from app.models import User, Question, Exam_Boards, Paper, Question_in, Exam_Levels, Tag
from app.main import bp
import json

#Grabs the current date and time when a user visited, happens before a view
@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

#main index page
@bp.route("/", methods=['GET', 'POST'])
@bp.route("/index", methods=['GET', 'POST'])
def index():
    return render_template("index.html", title="Home Page")

#handling a user page
@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user.deleted is not None:
        flash("User not found", 'danger')
    return render_template('user.html',user=user)

@bp.route('/edit_profile/<username>', methods=['GET','POST'])
@login_required
def edit_profile(username):
    form = EditProfileForm(current_user.username)
    #when a POST is sent, submit to check
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.name = form.name.data
        current_user.email = form.email.data
        current_user.school_name = form.school_name.data
        db.session.commit()
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('main.user',username=current_user.username))
    #when the form loads - GET, grab the data
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.name.data = current_user.name
        form.email.data = current_user.email
        form.school_name.data = current_user.school_name
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@bp.route('/delete_user/<id>')
@login_required
def delete_user(id):
    current_app.logger.info(id)
    user = User.query.get_or_404(id)
    if user.deleted is not None:
        flash("User not found")
    user.deleted = datetime.utcnow()
    db.session.commit()
    flash('Account has been deleted', 'success')
    return redirect(url_for('auth.logout'))

#split create paper and edit paper apart!!
@bp.route('/create_paper', methods=['GET','POST'])
@login_required
def create_paper():
    form = CreatePaperForm()
    form.exam_level.choices = [(el.id, el.name) for el in Exam_Levels.query.all()]
    paper = Paper()
    if form.validate_on_submit():
        form.populate_obj(paper)
        current_app.logger.info("TEST", json.dumps([]))
        paper.author = current_user
        #paper.total_marks = 0
        paper.positions = json.dumps([])
        db.session.add(paper)
        db.session.commit()
        flash('The paper was created. Please add questions', 'success')
        return redirect(url_for('main.edit_paper', paper_id=paper.id))
    return render_template('create_paper.html', title='Create Paper', form=form)

#view all papers and edit
@bp.route('/view_papers', methods=['GET', 'POST'])
@login_required
def view_papers():
    #for pagination
    page = request.args.get('page', 1, type=int)
    papers = Paper.query.filter(Paper.author == current_user).order_by(Paper.date_created.desc()).paginate(
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

#editing a paper
@bp.route('/edit_paper', methods=['GET', 'POST'])
@login_required
def edit_paper():

    paper = Paper.query.filter_by(id=request.args.get('paper_id', None)).first()    
    positions = json.loads(paper.positions)
    form = CreatePaperForm(obj=paper)
    form.exam_level.choices = [(el.id, el.name) for el in Exam_Levels.query.all()]
    title = "Edit Paper - " + paper.name
    #gets all questions that are not in the paper
    questions = paper.not_used()
    #return questions currently in a paper
    used_qs = []
    temp = []
    for question in paper.all_questions():
        used_qs.append(question.to_dict())
    
    #swaps the question positions based on the position value for each paper
    for item in positions:
        for dic in used_qs:
            if dic["id"] == item:
                temp.append(dic)
    used_qs = temp
    
    #submitting paper updates
    if form.validate_on_submit:
        form.populate_obj(paper)
        db.session.commit()

    #handling the adding of a question
    question = Question.query.filter_by(id=request.args.get('question_id',None)).first()
    if question is not None:
        if question in questions:
            paper.add(question)
            flash('The question was added.', 'success')
        else:
            paper.delete(question)  
            flash('The question was removed.', 'success')

        return redirect(url_for('main.edit_paper', paper_id=paper.id))
    return render_template('edit_paper.html', title=title, paper=paper, 
        questions=questions, used_qs=used_qs, positions=positions, form=form
    )

@bp.route("/update_positions", methods=['POST','GET'])
@login_required
def update_positions():
    data = request.args.to_dict("data")
    paper = Paper.query.filter_by(id=data.get("paper")).first_or_404()
    paper.positions = data.get("positions")
    db.session.commit()
    return '', 204

#Deleting paper
@bp.route("/delete_paper/<paper_id>", methods=['POST','GET'])
@login_required
def delete_paper(paper_id):
    paper = Paper.query.filter_by(id=paper_id).first_or_404()
    db.session.delete(paper)
    db.session.commit()
    flash("Paper deleted", 'success')
    return redirect(url_for('main.view_papers'))

#produce the printable paper
@bp.route("/paper_generator/<paper_id>", methods=['POST','GET'])
@login_required
def paper_generator(paper_id):
    paper = Paper.query.filter_by(id=paper_id).first_or_404()
    positions = json.loads(paper.positions)
    title = paper.name
    #get all the questions
    used_qs = []
    temp = []
    for question in paper.all_questions():
        used_qs.append(question.to_dict())
    #swaps the question positions based on the position value for each paper
    for item in positions:
        for dic in used_qs:
            if dic["id"] == item:
                temp.append(dic)
    used_qs = temp

    return render_template('paper_generator.html', paper_id=paper.id, title=title, used_qs=used_qs,
        positions=positions, paper=paper)

#view all questions - uses the index page but with a different view
@bp.route("/view_questions", methods=['GET', 'POST'])
@login_required
def view_questions():
    #for pagination
    page = request.args.get('page', 1, type=int)
    questions = Question.query.filter(Question.author==current_user).order_by(Question.timestamp.desc()).paginate(
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

#check if tags already exist or not
def add_tag(tag):
    existing_tag = Tag.query.filter(Tag.name==tag.lower()).one_or_none()
    if existing_tag is not None:
        return existing_tag
    else:
        new_tag = Tag()
        new_tag.name = tag.lower()
        return new_tag

#add question
@bp.route("/add_question", methods=['GET', 'POST'])
@login_required #using flask-login to require a login to view
def add_question():
    form = QuestionForm()
    #get all existing examboards from the exam_boards table
    form.exam_board.choices = [(eb.id, eb.name) for eb in Exam_Boards.query.all()]
    form.exam_level.choices = [(el.id, el.name) for el in Exam_Levels.query.all()]
    
    if form.validate_on_submit():
        question = Question(body=form.body.data,
                            answer_space=form.answer_space.data, 
                            author=current_user,
                            exam_level = form.exam_level.data, 
                            exam_board=form.exam_board.data, 
                            exam_year=form.exam_year.data,
                            exam_session=form.exam_session.data,
                            marks=form.marks.data, 
                            answer=form.answer.data,
                            )
        #collecting tags
        tags = form.tags.data
        current_app.logger.info(tags)
        for tag in tags:
            q_tag = add_tag(tag)
            question.tags.append(q_tag)
    
        db.session.add(question)
        db.session.commit()
        flash("Question has been added",'success')
        return redirect(url_for('main.index'))
    if "cancel" in request.form:
        return redirect(url_for('main.view_questions'))

    return render_template("add_edit_question.html", title="Create a new Question",\
         form=form, path="add_question")

#Editing questions
@bp.route("/edit_question/<question_id>", methods=['GET','POST'])
@login_required
def edit_question(question_id):
    question = Question.query.filter_by(id=question_id).first_or_404()
    form = QuestionForm()
    form.exam_board.choices = [(eb.id, eb.name) for eb in Exam_Boards.query.all()]
    form.exam_level.choices = [(el.id, el.name) for el in Exam_Levels.query.all()]

    if "cancel" in request.form:
        return redirect(url_for('main.view_questions'))
    if form.validate_on_submit():
        question.body = form.body.data
        question.answer_space = form.answer_space.data
        question.exam_board=form.exam_board.data
        question.exam_level = form.exam_level.data
        question.exam_year=form.exam_year.data
        question.exam_session=form.exam_session.data
        question.marks=form.marks.data
        question.answer=form.answer.data
        tags = form.tags.data
        for tag in tags:
            q_tag = add_tag(tag)
            if q_tag not in question.tags.all(): #don't add duplicate tags
                question.tags.append(q_tag)

        db.session.commit()
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('main.view_questions'))

    if request.method == 'GET':
        form.body.data = question.body 
        form.answer_space.data = question.answer_space
        form.exam_board.data = question.exam_board
        form.exam_level.data = question.exam_level
        form.tags.data = question.all_tags() #get tags
        form.exam_year.data = question.exam_year
        form.exam_session.data = question.exam_session
        form.marks.data = question.marks
        form.answer.data = question.answer

    return render_template('add_edit_question.html', title='Edit Question',\
         form=form, path="edit_question", question_id=question_id)

#Deleting question
@bp.route("/delete_question/<question_id>", methods=['POST','GET'])
@login_required
def delete_question(question_id):
    question = Question.query.filter_by(id=question_id).first_or_404()
    question.delete()
    db.session.commit()
    flash("Question deleted", 'success')
    return redirect(url_for('main.view_questions'))

#add exam level
@bp.route("/add_exam_level/<path:path>", methods=['GET', 'POST'])
@bp.route("/add_exam_level/<path:path>/<int:question_id>", methods=['GET', 'POST'])
@login_required #using flask-login to require a login to view
def add_exam_level(path, question_id=None):
    form = ExamLevelForm()
    if form.validate_on_submit():
        exam_level = Exam_Levels(name=form.name.data)
        db.session.add(exam_level)
        db.session.commit()
        flash("Exam Level has been added", 'success')
        return redirect(url_for('main.'+path, question_id=question_id))
    
    return render_template("add_exam_level.html", title="Add Exam Level", form=form,\
        path=path, question_id=question_id)

#add examboard
@bp.route("/add_exam_board/<path:path>", methods=['GET', 'POST'])
@bp.route("/add_exam_board/<path:path>/<int:question_id>", methods=['GET', 'POST'])
@login_required #using flask-login to require a login to view
def add_exam_board(path, question_id=None):
    form = ExamBoardForm()
    current_app.logger.info(path)
    if form.validate_on_submit():
        exam_board = Exam_Boards(name=form.name.data)
        db.session.add(exam_board)
        db.session.commit()
        flash("Exam Board has been added", 'success')
        return redirect(url_for('main.'+path, question_id=question_id))
    return render_template("add_exam_board.html", title="Add Exam Board", path=path,\
        question_id=question_id, form=form)
