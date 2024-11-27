from flask import Flask,render_template,request,url_for,redirect,jsonify,session,flash
from dbconnection.datamanipulation import *
import datetime

app=Flask(__name__)
app.secret_key='supersecretkey'

@app.route('/')
def hai():
    return render_template('index.html')

@app.route('/reg')
def reg():
    return render_template('reg.html')

@app.route('/register',methods=['post'])
def register():
    name=request.form['name']
    gender=request.form['gender']
    address=request.form['address']
    country=request.form['country']
    phonenumber=request.form['phonenumber']
    username=request.form['username']
    password=request.form['password']
    user=sql_edit_insert("insert into register values(NULL,?,?,?,?,?,?,?)",(name,gender,address,country,phonenumber,username+"@mymail.com",password))
    return redirect(url_for('reg'))


@app.route('/username')
def username():
    username=request.args.get('m')
    data=sql_query2("select * from register where username=?",[username+'@mymail.com'])
    if len(data)>0:
        msg='exist'
    else:
        msg='not exist'
    return jsonify({'valid':msg}) 

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/loginhere',methods=['post'])
def loginhere():
    username=request.form['username']
    password=request.form['password']
    user=sql_query2('select * from register where username=? and password=?',(username,password))

    if len(user)>0:
        session['id']=user[0][0]
        flash('login successfull')
        return render_template('home.html')
    else:
        flash('somthing went wrong')   
        return redirect(url_for('login'))

@app.route('/mail')
def mail():
    return render_template('mail.html')    

@app.route('/sendmail',methods=['post'])
def sendmail():
    receivername=request.form['receivername']
    message=request.form['message']
    subject=request.form['subject']
    date=datetime.date.today()
    time=datetime.datetime.now().strftime('%H:%M')
    user=sql_query2('select * from register where username=?',[receivername])
    receiverid=user[0][0]
    senderid=session['id']
    a=sql_edit_insert('insert into mail values(NULL,?,?,?,?,?,?,?)',(receiverid,senderid,message,subject,date,time,'pending'))
    return render_template('mail.html')
    


@app.route('/receivername')
def receivername():
    id=request.args.get('m')
    data=sql_query2("select * from register where username=?",[id])
    if len(data)>0:
        msg='exist'
    else:
        msg='not exist'
    return jsonify({'valid':msg})     

@app.route('/viewmsg')
def viewmsg():
    viewmsg=sql_query2('select register.username,mail. * from register inner join mail on register.id=mail.receiverid where senderid=? and status!=?',(session['id'],'deleted by sender'))
    return render_template('viewmsg.html',view=viewmsg)

@app.route('/deletemsg')
def deletemsg():
    msgid=request.args.get('uid')
    msg=sql_query2('select * from mail where id=?',[msgid])
    status=msg[0][7]
    if(status=='deleted by receiver'):
        row=sql_edit_insert('delete from mail where id=?',[msgid])
        return redirect(url_for('viewmsg'))
    else:
        u=sql_edit_insert('update mail set status=? where id=?',('deleted by sender',msgid))
        return redirect(url_for('viewmsg'))

@app.route('/receivemsg')
def receivemsg():
    inboxmsg=sql_query2('select register.username,mail.* from mail inner join register on register.id=mail.senderid where receiverid=? and mail.id not in (select messageid from trash_tb where userid=?) and status!=?',(session['id'],session['id'],'deleted by receiver'))
    return render_template('inbox.html',msg=inboxmsg)

@app.route("/movetotrash",methods=['post'])
def movetotrash():
    date=datetime.date.today()
    time=datetime.datetime.now().strftime('%H:%M')
    check=request.form.getlist('checkbox')
    for mid in check:
        trash=sql_edit_insert('insert into trash_tb values(NULL,?,?,?,?)',(mid,session['id'],date,time))
    return redirect(url_for('receivemsg'))

@app.route("/viewtrash")
def viewtrash():
    trash=sql_query2('select register.username,trash_tb.date,trash_tb.time,mail.* from(register inner join mail on register.id=mail.senderid) inner join  trash_tb on mail.id=trash_tb.messageid where userid=?',[session['id']])
    return render_template('viewtrash.html',view=trash)

@app.route("/deletTrash")
def deletTrash():
    msgid=request.args.get('trashid')
    trash=sql_edit_insert('delete from trash_tb where messageid=?',[msgid])
    msg=sql_query2('select * from mail where id=?',[msgid])
    status=msg[0][7]
    if(status == 'deleted by sender'):
        row=sql_edit_insert('delete from mail where receiverid=?',[session['id']])
        return redirect(url_for('viewtrash'))
    else:
        trashmsg=sql_edit_insert('update mail set status=? where id=?',('deleted by receiver',msgid))
    return redirect(url_for('viewtrash'))


@app.route('/forward')
def forward():
    uid=request.args.get('uid')
    msg=sql_query2('select * from mail where id=?',[uid])
    return render_template('forward.html',row=msg)

@app.route("/forwardaction",methods=['post'])
def forwardaction():
    senderid=session['id']
    receiver=request.form['receivername']
    row=sql_query2('select * from register where username=?',[receiver])
    subject=request.form['subject']
    message=request.form['message']
    date=datetime.date.today()
    time=datetime.datetime.now().strftime('%H:%M')
    receiverid=row[0][0]
    rows=sql_edit_insert('insert into mail values(NULL,?,?,?,?,?,?,?)',(receiverid,senderid,message,subject,date,time,'pending'))
    if rows>0:
        msg='send'
    else:
        msg='not send'
    return render_template('forward.html',row=row,msg=msg)

@app.route('/replay')
def replay():
    msgid=request.args.get('uid')
    data=sql_query2('select register.username,mail.senderid from register inner join mail on register.id=mail.senderid where mail.id=?',[msgid])
    return render_template('replay.html',row=data) 
    
@app.route('/replayaction',methods=['post'])
def replayaction():
    senderid=session['id']
    receiver=request.form['receivername']
    subject=request.form['subject']
    message=request.form['message']
    date=datetime.date.today()
    time=datetime.datetime.now().strftime('%H:%M')
    row=sql_query2('select * from register where Username=?',[receiver])
    receiverid=[0][0]
    data=sql_edit_insert('insert into mail values(NULL,?,?,?,?,?,?,?)',(receiverid,senderid,message,subject,date,time,'pending'))
    if data>0:
        msg='send'
    else:
        msg='not send'
    return render_template('replay.html',row=row,msg=msg)

@app.route('/update')
def update():
    userid=session['id']
    user=sql_query2('select * from register where id=?',[userid])
    return render_template('edit.html',edit=user)

@app.route("/editaction",methods=['post'])
def editaction():
    userid=request.form['id']
    name=request.form['name']
    address=request.form['address']
    gender=request.form['gender']
    country=request.form['country']
    phonenumber=request.form['phonenumber']
    username=request.form['username']
    password=request.form['password']
    user=sql_edit_insert('update register set name=?,Address=?,Gender=?,Country=?,Phonenumber=?,Username=?,Password=? where id=?',(name,gender,address,country,phonenumber,username,password,userid))
    return render_template('index.html')

@app.route("/logout")
def logout():
    session.clear()
    flash('logging out')
    return render_template('index.html')


 















if __name__=='__main__':
    app.run(debug=True)