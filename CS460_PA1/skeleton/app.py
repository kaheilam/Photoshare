######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for, flash
from flaskext.mysql import MySQL
import flask_login
from datetime import datetime

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'secret'  # Change this!


#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Lkh1999426.'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)


#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()


def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()


class User(flask_login.UserMixin):
	pass


@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user


@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"


@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')


@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')


#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')


@app.route("/register", methods=['POST'])
def register_user():
	email=request.form.get('email')
	password=request.form.get('password')
	firstname=request.form.get('firstname')
	lastname=request.form.get('lastname')
	birthday=request.form.get('birthday')
	gender=request.form.get('gender')
	hometown=request.form.get('hometown')
	# except:
	# 	print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
	# 	flash("Please enter all the information")
	# 	return flask.redirect(flask.url_for('register'))

	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (first_name, last_name, email, birth_date, hometown, gender, password, cpoint) \
			VALUES ('{0}', '{1}','{2}','{3}','{4}','{5}','{6}','{7}')".format(firstname, lastname, email, birthday, hometown, gender, password, 0)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		flash("Email already in use, please try again!")
		return flask.redirect(flask.url_for('register'))


@app.route("/friend")
@flask_login.login_required
def friend():
	email = flask_login.current_user.id
	cursor = conn.cursor()
	cursor.execute(("SELECT first_name, last_name, email FROM Users WHERE Users.user_id in\
					(SELECT F.user_id2 \
			 		  FROM Users as U, Friends as F \
			 		  WHERE email = '{0}' and U.user_id = F.user_id1)".format(email)))
	data = cursor.fetchall()
	return render_template("friends.html", data=data, email=email)


@app.route("/addfriend", methods = ["POST", "GET"])
@flask_login.login_required
def addfriend():
	if request.method == "POST":
		# Check if the user clicked "add" button
		if "add" in request.form:
			email = request.form.get("email")
			# Check if email is empty
			if email != "":
				# Check if user exist
				if (isEmailUnique(email)):
					flash("No such user")
					return redirect(url_for("addfriend"))
				else:
					user1 = getUserIdFromEmail(flask_login.current_user.id)
					user2 = getUserIdFromEmail(email)
					cursor = conn.cursor()
					isFriend = "SELECT COUNT(*) FROM Friends WHERE user_id1 = '{0}' and user_id2 = '{1}'".format(user1, user2)
					cursor.execute(isFriend)
					data = cursor.fetchall()
					# Check if the user is already frined
					if user1 == user2:
						flash("You cannot add yourself")
						return redirect(url_for("addfriend"))
					if int(data[0][0]) == 0:
						cursor.execute("INSERT INTO Friends(user_id1, user_id2) VALUES ('{0}','{1}')".format(user1, user2))
						conn.commit()
						flash("Users has been added to your friend list!")
						return redirect(url_for("addfriend"))
					else:
						flash("The User is already in your friend list")
						return redirect(url_for("addfriend"))			
			else:
				flash("Please enter email")
				return redirect(url_for("addfriend"))
		# The user clicked "search" button
		else:
			firstname = request.form.get("firstname")
			# Check if firstname is empty
			if firstname == "":
				flash("Please enter firstname")
				return redirect(url_for("addfriend"))
			else:
				cursor = conn.cursor()
				cursor.execute("SELECT * FROM Users WHERE first_name = '{0}'".format(firstname))
				data = cursor.fetchall()
				if data:
					return render_template("addfriend.html",data=data)
				else:
					return render_template("addfriend.html",noresult=True)
	return render_template("addfriend.html")


def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]


def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]


def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code


@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")


#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':	
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		album = request.form.get('album')	
		cursor = conn.cursor()
		# Check if album exist and belongs to user
		cursor.execute("SELECT COUNT(*) FROM Albums WHERE albums_id='{0}' and user_id='{1}'".format(album, uid))
		data = cursor.fetchall()
		if int(data[0][0]) == 0:
			flash("Album is not in your album list")
			return redirect(url_for("upload_file"))
		else:
			cursor.execute('''INSERT INTO Photos (caption, data, user_id, albums_id) VALUES (%s, %s, %s ,%s)''' ,(caption, photo_data,uid,album))
			conn.commit()
			addpoint(uid)
			cursor.execute("SELECT MAX(photo_id) FROM Photos")
			photo_id = cursor.fetchall()
			tag_temp = request.form.get('tag')
			# insert tag if its not none
			if tag_temp != "":
				tag = tag_temp.split()
				for item in tag:
					insertTagged(item, int(photo_id[0][0]))
			return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid),base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		cursor = conn.cursor()
		cursor.execute("SELECT albums_id, name, date FROM Albums WHERE user_id = '{0}'".format(uid))
		data = cursor.fetchall()
		return render_template('upload.html', data=data)
#end photo uploading code


@app.route('/myalbum', methods = ["POST", "GET"])
@flask_login.login_required
def myalbum():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	if request.method == "POST":
		# If the user clicked "Add"
		if "addbutton" in request.form:
			album = request.form.get("album")
			if album == "":
				flash("Please enter an album name")
				return redirect(url_for("myalbum"))
			else: 
				today = datetime.today().strftime('%Y-%m-%d')
				uid = getUserIdFromEmail(flask_login.current_user.id)
				cursor.execute("INSERT INTO Albums(name, date, user_id) VALUES ('{0}','{1}','{2}')".format(album, today, uid))
				conn.commit()
				flash("New album has been added!")
		# View click "Delete"
		elif "deletebutton" in request.form:
			delete = request.form.get("delete")
			if delete == "":
				flash("Please enter an album id")
				return redirect(url_for("myalbum"))
			else: 
				cursor.execute("SELECT COUNT(*) FROM Albums WHERE albums_id='{0}' and user_id='{1}'".format(delete, uid))
				data = cursor.fetchall()
				if int(data[0][0]) == 0:
					flash("Album is not in your album list")
					return redirect(url_for("myalbum"))
				else:
					cursor.execute("DELETE FROM Albums WHERE albums_id = '{0}'".format(delete))
					conn.commit()
					flash("Album and its photos have been deleted")
					return redirect(url_for("myalbum"))
		# The user click "View"
		else:
			return "view"#return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid),base64=base64)
	# if GET
	cursor.execute("SELECT albums_id, name, date FROM Albums WHERE user_id = '{0}'".format(uid))
	data = cursor.fetchall()
	return render_template("myalbum.html", data=data, email = flask_login.current_user.id)


@app.route("/photos")
def photos():
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos")
	photos = cursor.fetchall()
	return render_template('photos.html', photos=photos,base64=base64)


@app.route("/delete", methods=["POST","GET"])
@flask_login.login_required
def delete():
	if request.method == "POST":
		pid = request.form.get("photo")
		cursor = conn.cursor()
		cursor.execute("SELECT COUNT(*) FROM Photos as P WHERE P.photo_id = '{0}'".format(pid))
		data = cursor.fetchall()
		if int(data[0][0]) == 0:
			flash("This photo is not in your album")
			return redirect(url_for("delete"))
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor.execute("DELETE FROM Photos as P WHERE P.user_id = {0} AND\
					 P.photo_id = '{1}'".format(uid, pid))
		conn.commit()
		flash("Photo has been delete!")
		return redirect(url_for("delete"))
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute(" SELECT P.data, P.photo_id, P.caption \
					FROM Photos as P WHERE P.user_id = {0}".format(uid))
	photos = cursor.fetchall()
	return render_template('delete.html', photos=photos,base64=base64)


def insertTagged(tag, photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT tag_id FROM Tags WHERE word = '{0}'".format(tag))
	tag_id = cursor.fetchone()
	# check if tag exist
	if tag_id is None:
		cursor.execute("INSERT INTO Tags(word) VALUES ('{0}')".format(tag))
		conn.commit()
	cursor.execute("SELECT tag_id FROM Tags WHERE word = '{0}'".format(tag))
	tag_id = cursor.fetchone()
	cursor.execute("INSERT INTO Tagged(photo_id, tag_id) VALUES('{0}','{1}')".format(photo_id, tag_id[0]))
	conn.commit()
	return 


@app.route("/tags")
def tags():
	cursor = conn.cursor()
	cursor.execute("SELECT DISTINCT T.tag_id, T.word FROM Tags as T, Tagged as Ta WHERE T.tag_id = Ta.tag_id")
	data = cursor.fetchall()
	return render_template("tags.html", data=data)


@app.route("/tags/<tag>")
def tag(tag):
	cursor = conn.cursor()
	cursor.execute("SELECT P.data, P.photo_id, P.caption \
					FROM Photos as P, Tagged as Ta, Tags as T \
					WHERE P.photo_id = Ta.photo_id and Ta.tag_id = T.tag_id and T.word = '{0}'".format(tag))
	data = cursor.fetchall()
	if len(data) == 0:
		flash("No result")
		return redirect(url_for("/tags"))
	else:
		return render_template('view.html', photos=data,base64=base64)


@app.route("/populartags")
def populartags():
	cursor = conn.cursor()
	cursor.execute("SELECT * \
					FROM Tagged as Ta, Tags as T\
					WHERE Ta.tag_id = T.tag_id\
					Group by T.word\
					Order by Count(*) DESC;")

	data = cursor.fetchall()
	return render_template("populartags.html", data=data)


@app.route("/mytags")
@flask_login.login_required
def mytags():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT T.word\
					FROM Photos as P, Tagged as Ta, Tags as T\
					WHERE  P.photo_id = Ta.photo_id \
					and Ta.tag_id = T.tag_id and P.user_id = '{0}'\
					group by Ta.tag_id".format(uid))
	data = cursor.fetchall()
	return render_template("mytags.html", data=data)


@app.route("/mytags/<tag>")
@flask_login.login_required
def mytag(tag):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT P.data, P.photo_id, P.caption\
					FROM Photos as P, Tagged as Ta, Tags as T\
					WHERE  P.photo_id = Ta.photo_id \
					and Ta.tag_id = T.tag_id and P.user_id = {0} \
					and T.word = '{1}'".format(uid,tag))

	data = cursor.fetchall()
	return render_template('view.html', photos=data,base64=base64)


@app.route("/photosearch", methods=["POST", "GET"])
def photoSearch():
	if request.method == "POST":
		l = (request.form.get("tag")).split()
		n = len(l)
		temp = []
		data = []
		cursor = conn.cursor()
		for item in l:
			cursor.execute("SELECT P.photo_id, T.word\
							FROM Photos as P, Tagged as Ta, Tags as T\
							WHERE  P.photo_id = Ta.photo_id \
							and Ta.tag_id = T.tag_id  and T.word = '{0}'".format(item))
			for i in cursor:
				temp.append(i)

		dictionary = dict()
		for i in temp:
			photo_id = i[0]
			if dictionary.get(photo_id) is None:
				dictionary[photo_id] = 1
			else:
				dictionary[photo_id] += 1
			if dictionary.get(photo_id) == n:
				data.append(photo_id)

		final = []
		for item in data:
			cursor.execute("SELECT data, photo_id, caption \
							FROM Photos WHERE photo_id = '{0}'".format(item))
			for i in cursor:
				final.append(i)

		return render_template("photosearch.html", photos=final,base64=base64)

	return render_template("photosearch.html")


# function for comment/like section
@app.route("/comments/<photo_id>", methods=["POST", "GET"])
def comment(photo_id):
	if request.method == "POST":
		pid = photo_id[1:-1]
		if "commentbutton" in request.form:
			comment = request.form.get("comment")
			if comment == "":
				flash("Cannot add an empty comment")
				return redirect(url_for('comment', photo_id=pid))
			else:
				today = datetime.today().strftime('%Y-%m-%d')
				if isUser():
					# cannot comment own photo
					if selfComment(pid):
						flash("Cannot comment on your own photo")
						return redirect(url_for('comment', photo_id=pid))
					else:
						uid = getUserIdFromEmail(flask_login.current_user.id)
						cursor = conn.cursor()
						cursor.execute("INSERT INTO Comments(user_id, photo_id, text, date)\
										VALUES ({0},{1},'{2}','{3}')".format(uid, pid, comment, today))
						conn.commit()
						addpoint(uid)

				# Else the user is anonymous
				else: 
					cursor = conn.cursor()
					cursor.execute("INSERT INTO Comments(photo_id, text, date) \
									VALUES ({0},'{1}','{2}')".format(pid, comment, today))
					conn.commit()
				flash("Comment has been added")
				return redirect(url_for('comment', photo_id=pid))

		# The person liked the photo
		else:
			if isUser():
				uid = getUserIdFromEmail(flask_login.current_user.id)
				cursor = conn.cursor()
				cursor.execute("INSERT INTO Likes(photo_id, user_id) VALUES('{0}','{1}')".format(pid, uid))
				conn.commit()
				flash("You liked this photo!!")
				return redirect(url_for('comment', photo_id=pid))
			else:
				flash("You cannot like this photo as an anonymous user")
				return redirect(url_for('comment', photo_id=pid))

	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE photo_id = {0}".format(photo_id))
	photo = cursor.fetchall()
	cursor.execute("SELECT text FROM Comments WHERE photo_id = {0}".format(photo_id))
	data = cursor.fetchall()
	cursor.execute("SELECT COUNT(*) FROM Likes WHERE photo_id = {0}".format(photo_id))
	like = cursor.fetchall()
	cursor.execute("SELECT U.email FROM Users as U, Likes as L \
					WHERE U.user_id = L.user_id and L.photo_id={0}".format(photo_id))
	usersliked = cursor.fetchall()
	return render_template("comment.html", photo=photo[0], base64=base64, data=data, like=like[0][0], usersliked=usersliked)


def addpoint(uid):
	cursor = conn.cursor()
	cursor.execute("UPDATE Users SET cpoint = cpoint+1 WHERE Users.user_id = {0}".format(uid))
	conn.commit()
	return


# Find Top 10 users with highest contribution points
@app.route("/activity")
def activity():
	cursor = conn.cursor()
	cursor.execute("SELECT email, cpoint FROM Users WHERE cpoint <> 0 ORDER BY cpoint DESC LIMIT 10")
	data = cursor.fetchall()
	return render_template("activity.html", data=data)


# Search On Comment
@app.route("/searchC", methods=["POST", "GET"])
def searchC():
	if request.method == "POST":
		comment = request.form.get("comment")
		cursor = conn.cursor()
		cursor.execute("SELECT U.email, COUNT(*)\
						FROM Users as U, Comments as C\
						WHERE U.user_id = C.user_id and C.text = '{0}'\
						GROUP BY U.user_id\
						ORDER BY COUNT(*) DESC".format(comment))
		data=cursor.fetchall()
		return render_template("searchC.html", data=data)

	return render_template("searchC.html")


# Freind Recommendation
@app.route("/recom")
@flask_login.login_required
def recom():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT U.email, COUNT(*) FROM Users as U,\
						(SELECT FF.user_id2\
						FROM Friends AS F, Friends AS FF\
						WHERE F.user_id2 = FF.user_id1 and F.user_id1 <> FF.user_id2 and F.user_id1 = {0}\
						and FF.user_id2 NOT IN\
							(SELECT user_id2 FROM Friends WHERE user_id1 = {0})) AS T\
							WHERE U.user_id = T.user_id2\
							GROUP BY user_id\
							ORDER BY COUNT(*) DESC".format(uid))
	data=cursor.fetchall()
	return render_template("recom.html", data=data)


# T/F if a user logged in
def isUser():
	try:
		flask_login.current_user.id
	except:
		return False
	return True


# T/F if users are commenting their own photo
def selfComment(pid):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) \
					FROM Users as U, Photos as P \
					WHERE U.user_id = P.user_id and U.user_id = {0} and P.photo_id = {1}".format(uid, pid))
	data = cursor.fetchall()
	if int(data[0][0]) == 0:
		return False
	return True


# 'You-may-also-like' functionality
@app.route("/alsolike")
@flask_login.login_required
def alsolike():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT P.data, P.photo_id, P.caption\
					FROM Photos as P, Tagged as T,\
						(SELECT T.tag_id\
						FROM Photos as P, Tagged as Ta, Tags as T\
						WHERE P.user_id = {0} and P.photo_id = Ta.photo_id and Ta.tag_id = T.tag_id\
						Group by T.tag_id\
						ORDER BY COUNT(*) DESC LIMIT 5) as Temp\
					WHERE P.photo_id = T.photo_id and T.tag_id = Temp.tag_id\
					GROUP BY P.photo_id\
					ORDER BY COUNT(*) DESC".format(uid))
	data=cursor.fetchall()
	return render_template("alsolike.html", photos=data, base64=base64)


@app.route("/")
def hello():
	return render_template("hello.html")


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
