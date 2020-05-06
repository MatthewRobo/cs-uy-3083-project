#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import os
from datetime import datetime

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='',
                       db='finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    email = request.form['email']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, password, firstName, lastName, email))
        conn.commit()
        cursor.close()
        return render_template('index.html')

@app.route('/home')
def home():
    userID = session['username']
    cursor = conn.cursor();
    #First query before the union is for finding all visible posts posted by other people
    #Second query is for finding all visible posts posted by the logged in user
    #Third query is for finding all visibnle posts posted in a FriendGroup that the logged in user belongs to
    query = 'SELECT firstName, lastName, postingDate, pID \
             FROM Photo INNER JOIN Follow ON Photo.poster = Follow.followee, Person \
             WHERE follower = %s AND followStatus = 1 AND username = poster AND allFollowers = 1 \
             UNION \
             SELECT firstName, lastName, postingDate, pID \
             FROM Photo, Person \
             WHERE Photo.poster = %s AND Person.username = Photo.poster \
             UNION \
             SELECT firstName, lastName, postingDate, SharedWith.pID \
             FROM FriendGroup AS F, BelongTo AS B, SharedWith, Photo, Person \
             WHERE F.groupName = B.groupName AND F.groupCreator = B.groupCreator AND SharedWith.groupName = F.groupName AND \
                SharedWith.groupCreator = F.groupCreator AND SharedWith.pID = Photo.pID AND F.groupCreator = Person.username AND \
                B.username = %s \
             ORDER BY postingDate DESC'
    cursor.execute(query, (userID, userID, userID))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=userID, posts=data)

@app.route('/tagged')
def tagged():
    userID = session['username']
    cursor = conn.cursor();
    #First query before the union is for finding all visible posts with tags posted by other people
    #Second query is for finding all visible posts with tags posted by the logged in user
    #Third query is for finding all visibnle posts with tags posted in a FriendGroup that the logged in user belongs to
    query = 'SELECT tag.pID, tag.username, T.firstName, T.lastName \
             FROM (Photo INNER JOIN Follow ON Photo.poster = Follow.followee), Person AS P, Person AS T, Tag \
             WHERE follower = %s AND followStatus = 1 AND P.username = Photo.poster AND allFollowers = 1 AND Tag.pID = Photo.pID AND \
                Tag.username = T.username AND tagStatus = 1 \
             UNION \
             SELECT DISTINCT tag.pID, tag.username, T.firstName, T.lastName \
             FROM Photo, Follow, Person AS P, Person AS T, Tag \
             WHERE Photo.poster = %s AND Photo.poster = P.username AND Tag.pID = Photo.pID AND Tag.username = T.username AND tagStatus = 1 \
             UNION \
             SELECT SharedWith.pID, Tag.username, taggee.firstName, taggee.lastName \
             FROM FriendGroup AS F, BelongTo AS B, SharedWith, Photo, Person AS gCreator, Person AS taggee, Tag \
             WHERE F.groupName = B.groupName AND F.groupCreator = B.groupCreator AND SharedWith.groupName = F.groupName AND \
                SharedWith.groupCreator = F.groupCreator AND SharedWith.pID = Photo.pID AND F.groupCreator = gCreator.username AND \
                B.username = %s AND SharedWith.pID = Tag.pID AND tagStatus = 1 AND taggee.username = Tag.username'
    cursor.execute(query, (userID, userID, userID))
    data = cursor.fetchall()
    cursor.close()
    return render_template('tagged.html', username=userID, posts=data)

@app.route('/reactedTo')
def reactedTo():
    userID = session['username']
    cursor = conn.cursor();
    #First query before the union is for finding all visible posts with reactions posted by other people
    #Second query is for finding all visible posts with reactions posted by the logged in user
    #Third query is for finding all visibnle posts with reactions posted in a FriendGroup that the logged in user belongs to
    query = 'SELECT ReactTo.username, Photo.pID, comment, emoji \
             FROM (Photo INNER JOIN Follow ON Photo.poster = Follow.followee), Person, ReactTo \
             WHERE follower = %s AND followStatus = 1 AND Person.username = poster AND allFollowers = 1 AND ReactTo.pID = Photo.pID \
             UNION\
             SELECT ReactTo.username, Photo.pID, comment, emoji \
             FROM Photo, ReactTo \
             WHERE Photo.poster = %s AND ReactTo.pID = Photo.pID \
             UNION \
             SELECT ReactTo.username, Photo.pID, COMMENT, emoji \
             FROM FriendGroup AS F, BelongTo AS B, SharedWith, Photo, Person, ReactTo \
             WHERE F.groupName = B.groupName AND F.groupCreator = B.groupCreator AND SharedWith.groupName = F.groupName AND \
                SharedWith.groupCreator = F.groupCreator AND SharedWith.pID = Photo.pID AND F.groupCreator = Person.username AND \
                B.username = %s AND SharedWith.pID = ReactTo.pID'
    cursor.execute(query, (userID, userID, userID))
    data = cursor.fetchall()
    cursor.close()
    return render_template('reactedTo.html', username=userID, posts=data)

@app.route('/search_by_tag')
def search_by_tag():
    return render_template('search_by_tag.html')

@app.route('/search_tag', methods=['GET', 'POST'])
def search_tag():
    # Extra feature 9
    # Implemented by Simon Oh
    # Searches through all the photos that are visible to the user by the people who are tagged
    userID = session['username']
    taggedPersonID = request.form['taggedPersonID']
    cursor = conn.cursor()
    # First query is for searching for tags in the photos that other people posted
    query = 'SELECT pID \
             FROM (Photo INNER JOIN Follow ON Photo.poster = Follow.followee), Person \
             WHERE follower = %s AND followStatus = 1 AND Person.username = poster AND allFollowers = 1 AND pID IN \
             (SELECT pID \
             FROM Photo NATURAL JOIN Tag \
             WHERE tagStatus = 1 AND username = %s)'
    cursor.execute(query, (userID, taggedPersonID))
    data = cursor.fetchone()
    # Second query is for searching for tags in the photos that I posted
    query2 = 'SELECT pID \
              FROM Photo, Person \
              WHERE Photo.poster = %s AND Person.username = Photo.poster AND Photo.pID IN \
              (SELECT Photo.pID \
              FROM Photo NATURAL JOIN Tag \
              WHERE tagStatus = 1 AND username = %s)'
    cursor.execute(query2, (userID, taggedPersonID))
    data2 = cursor.fetchone()
    # Third query is for searching for tags in the photos that are shared in the FriendGroup that I belong in
    query3 = 'SELECT SharedWith.pID \
              FROM FriendGroup AS F, BelongTo AS B, SharedWith, Photo, Person \
              WHERE F.groupName = B.groupName AND F.groupCreator = B.groupCreator AND SharedWith.groupName = F.groupName AND \
              SharedWith.groupCreator = F.groupCreator AND SharedWith.pID = Photo.pID AND F.groupCreator = Person.username AND \
              B.username = %s AND Photo.pID IN( SELECT Photo.pID FROM Photo NATURAL JOIN Tag WHERE tagStatus = 1 AND username = %s)'
    cursor.execute(query3, (userID, taggedPersonID))
    data3 = cursor.fetchone()
    error = None
    if(data or data2 or data3):
        query = 'SELECT firstName, lastName, postingDate, pID \
                 FROM (Photo INNER JOIN Follow ON Photo.poster = Follow.followee), Person \
                 WHERE follower = %s AND followStatus = 1 AND Person.username = poster AND allFollowers = 1 AND pID IN \
                 (SELECT pID \
                 FROM Photo NATURAL JOIN Tag \
                 WHERE tagStatus = 1 AND username = %s) \
                 UNION \
                 SELECT firstName, lastName, postingDate, pID \
                 FROM Photo, Person \
                 WHERE Photo.poster = %s AND Person.username = Photo.poster AND Photo.pID IN \
                 (SELECT Photo.pID \
                 FROM Photo NATURAL JOIN Tag \
                 WHERE tagStatus = 1 AND username = %s) \
                 UNION \
                 SELECT firstName, lastName, postingDate, SharedWith.pID \
                 FROM FriendGroup AS F, BelongTo AS B, SharedWith, Photo, Person \
                 WHERE F.groupName = B.groupName AND F.groupCreator = B.groupCreator AND SharedWith.groupName = F.groupName AND \
                    SharedWith.groupCreator = F.groupCreator AND SharedWith.pID = Photo.pID AND F.groupCreator = Person.username AND \
                    B.username = %s AND Photo.pID IN \
                    (SELECT Photo.pID FROM Photo NATURAL JOIN Tag WHERE tagStatus = 1 AND username = %s)'
        cursor.execute(query, (userID, taggedPersonID, userID, taggedPersonID, userID, taggedPersonID))
        data = cursor.fetchall()
        conn.commit()
        cursor.close()
        return render_template('search_by_tag.html', posts=data)
    else:
        error = "There are no photos visible to you with person " + taggedPersonID + " tagged."
        cursor.close()
        return render_template('search_by_tag.html', error = error)

@app.route('/search_by_poster')
def search_by_poster():
    return render_template('search_by_poster.html')

@app.route('/search_poster', methods=['GET', 'POST'])
def search_poster():
    # Extra feature 10
    # Implemented by Simon Oh
    # Searches through all the photos that are visible to the user by the people who posted them
    userID = session['username']
    posterID = request.form['posterID']
    cursor = conn.cursor()
    # First query is for searching by usernames in the photos that other people posted
    query = 'SELECT pID \
             FROM (Photo INNER JOIN Follow ON Photo.poster = Follow.followee), Person \
             WHERE follower = %s AND followStatus = 1 AND Person.username = poster AND allFollowers = 1 AND pID IN \
             (SELECT pID \
             FROM Photo \
             WHERE poster = %s)'
    cursor.execute(query, (userID, posterID))
    data = cursor.fetchone()
    # Second query is for searching by usernames in the photos that I posted
    query2 = 'SELECT pID \
              FROM Photo, Person \
              WHERE Photo.poster = %s AND Person.username = Photo.poster AND Photo.pID IN \
              (SELECT pID \
              FROM Photo \
              WHERE poster = %s)'
    cursor.execute(query2, (userID, posterID))
    data2 = cursor.fetchone()
    query3 = 'SELECT SharedWith.pID \
              FROM FriendGroup AS F, BelongTo AS B, SharedWith, Photo, Person \
              WHERE F.groupName = B.groupName AND F.groupCreator = B.groupCreator AND SharedWith.groupName = F.groupName AND \
                SharedWith.groupCreator = F.groupCreator AND SharedWith.pID = Photo.pID AND F.groupCreator = Person.username AND \
                B.username = %s AND Photo.pID IN \
                (SELECT pID FROM Photo WHERE poster = %s)'
    cursor.execute(query3, (userID, posterID))
    data3 = cursor.fetchone()
    error = None
    if(data or data2 or data3):
        query = 'SELECT firstName, lastName, postingDate, pID \
                 FROM (Photo INNER JOIN Follow ON Photo.poster = Follow.followee), Person \
                 WHERE follower = %s AND followStatus = 1 AND Person.username = poster AND allFollowers = 1 AND pID IN \
                 (SELECT pID \
                 FROM Photo \
                 WHERE poster = %s) \
                 UNION \
                 SELECT firstName, lastName, postingDate, pID \
                 FROM Photo, Person \
                 WHERE Photo.poster = %s AND Person.username = Photo.poster AND Photo.pID IN \
                 (SELECT pID \
                 FROM Photo \
                 WHERE poster = %s) \
                 UNION \
                 SELECT firstName, lastName, postingDate, SharedWith.pID \
                 FROM FriendGroup AS F, BelongTo AS B, SharedWith, Photo, Person \
                 WHERE F.groupName = B.groupName AND F.groupCreator = B.groupCreator AND SharedWith.groupName = F.groupName AND \
                    SharedWith.groupCreator = F.groupCreator AND SharedWith.pID = Photo.pID AND F.groupCreator = Person.username AND \
                    B.username = %s AND Photo.pID IN \
                    (SELECT pID FROM Photo WHERE poster = %s)'
        cursor.execute(query, (userID, posterID, userID, posterID, userID, posterID))
        data = cursor.fetchall()
        conn.commit()
        cursor.close()
        return render_template('search_by_poster.html', posts=data)
    else:
        error = "There are no photos visible to you with poster ID " + posterID + "."
        return render_template('search_by_poster.html', error = error)

@app.route ('/post')
def post():
    return render_template("postphoto.html")

@app.route('/post_photo', methods=['GET', 'POST'])
def post_photo():
    username = session['username']
    photoID = request.form['pID']
    allFollowers = request.form['allFollowers']
    caption = request.form['caption']
    upload_folder = "C:\databases_project\cs-uy-3083-project-master\images"
    now = datetime.now()

    file = request.files['inputFile']
    filename = photoID + "." + file.filename.rsplit('.', 1)[1].lower()
    print(filename)

    cursor = conn.cursor()

    query = 'SELECT * FROM photo WHERE pID = %s'
    cursor.execute(query, (photoID))

    data = cursor.fetchone()

    error = None
    if (data):
        error = "This post ID already exists."
        return render_template('postphoto.html', error=error)
    else:
        query = 'INSERT INTO photo (pID, postingDate, filePath, allFollowers, caption, poster) VALUES(%s, %s, %s, %s, %s, %s)'
        cursor.execute(query, (photoID, now.strftime('%Y-%m-%d %H:%M:%S'), filename, allFollowers, caption, username))
        file.save(os.path.join(upload_folder, filename))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

# Extra feature pre-11
# Implemented by Matthew Nguyen (mdn296)
# Displays friendgroups to user
@app.route('/show_friendgroups')
def show_friendgroups():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT fg.groupName AS groupN, fg.description AS description, \
                    bt.username AS friend, p.firstName AS firstName, p.lastName AS lastName\
             FROM friendgroup AS fg \
             LEFT JOIN belongto AS bt ON fg.groupName = bt.groupName AND fg.groupCreator = bt.groupCreator \
             LEFT JOIN person AS p ON bt.username = p.username \
             WHERE fg.groupCreator = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_friendgroups.html', groups=data)

# Extra feature 11
# Implemented by Matthew Nguyen (mdn296)
# Adds and remove friends from friend group
@app.route('/add_friend', methods=['GET', 'POST'])
def add_friend():
    username = session['username']
    fgroup = request.form['groupName']
    friend = request.form['friendName']
    addrem = request.form['addrem'] # Add/Removal flag, add is '+', remove is '-'

    cursor = conn.cursor()
    # Finds if friend already exists in the group
    query = 'SELECT * FROM belongto \
             WHERE groupCreator = %s \
             AND groupName = %s \
             AND username = %s '
    cursor.execute(query, (username, fgroup, friend))
    data = cursor.fetchone()
    error = None

    # Finds all friendgroups and friends
    query = 'SELECT fg.groupName AS groupN, fg.description AS description, \
                    bt.username AS friend, p.firstName AS firstName, p.lastName AS lastName\
             FROM friendgroup AS fg \
             LEFT JOIN belongto AS bt ON fg.groupName = bt.groupName AND fg.groupCreator = bt.groupCreator \
             LEFT JOIN person AS p ON bt.username = p.username \
             WHERE fg.groupCreator = %s'
    if(data):
        if (addrem == '-'):
            status = "%s was removed from %s." % (friend, fgroup)
            deletthis = 'DELETE FROM belongto WHERE username = %s AND groupName = %s AND groupCreator = %s'
            cursor.execute(deletthis, (friend, fgroup, username))
            cursor.execute(query, (username))
            data2 = cursor.fetchall()
            cursor.close()
            return render_template('show_friendgroups.html', groups = data2, status = status)

        else:
            # If the first query returns data, then user exists
            error = "%s is already in %s." % (friend, fgroup)
            cursor.execute(query, (username))
            data2 = cursor.fetchall()
            return render_template('show_friendgroups.html', groups = data2, error = error)
    else:
        if (username == friend):
            error = "Cannot add yourself to your own group."
            cursor.execute(query, (username))
            data2 = cursor.fetchall()
            return render_template('show_friendgroups.html', groups = data2, error = error)

        else:
            ins = 'INSERT INTO belongto VALUES(%s, %s, %s)'
            status = "%s was added to %s." % (friend, fgroup)
            cursor.execute(ins, (friend, fgroup, username))
            conn.commit()
            cursor.execute(query, (username))
            data2 = cursor.fetchall()
            cursor.close()
            return render_template('show_friendgroups.html', groups = data2, status = status)



@app.route('/select_user')
def select_user():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    
    cursor = conn.cursor();
    query = 'SELECT DISTINCT username FROM photo'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('user.html', user_list=data)

@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    cursor = conn.cursor();
    query = 'SELECT ts, pID FROM photo WHERE username = %s ORDER BY ts DESC'
    cursor.execute(query, poster)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_posts.html', poster_name=poster, posts=data)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'test test test 145'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
