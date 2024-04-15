import pandas as pd
from flask import Flask, render_template, request, session,url_for,redirect
from mysql.connector import cursor
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
import mysql
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import xgboost as xgb

# from password_validation import PasswordPolicy, CharacterPool
from flask import flash

def preprocessing(file):
    enc = LabelEncoder()
    file['Hospital_type_code'] = enc.fit_transform(file['Hospital_type_code'])
    file['Hospital_region_code'] = enc.fit_transform(file['Hospital_region_code'])
    file['Department'] = enc.fit_transform(file['Department'])
    file['Ward_Type'] = enc.fit_transform(file['Ward_Type'])
    file['Ward_Facility_Code'] = enc.fit_transform(file['Ward_Facility_Code'])
    file['Type of Admission'] = enc.fit_transform(file['Type of Admission'])
    file['Severity of Illness'] = enc.fit_transform(file['Severity of Illness'])
    file['Age']=file['Age'].replace({'0-10': 10, '11-20': 20, '21-30': 30, '31-40': 40, '41-50': 50, '51-60': 60, '61-70': 70,'71-80':80,'81-90': 90, '91-100': 100})
    file['City_Code_Patient'].fillna(value=file['City_Code_Patient'].median(), inplace=True)

    file['Bed Grade'].fillna(value=file['Bed Grade'].median(), inplace=True)
    file.drop(['Hospital_type_code', 'City_Code_Hospital', 'Hospital_region_code', 'Ward_Facility_Code'], axis=1,
            inplace=True)
    return file
#
# hex_pool = CharacterPool(
#     lowercase="",
#     uppercase="ABCDEF",
#     numbers="0123456789",
#     symbols="",
#     whitespace="",
#     other="",
# )
# policy = PasswordPolicy(character_pool=hex_pool)
mydb=mysql.connector.connect(host='localhost',user='root',password='@Aditya82',port='3306',database='health')
app=Flask(__name__)
app.secret_key = 'many random bytes'
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/upload',methods=['GET','POST'])
def upload():
    if request.method=="POST":
        try:
            file=request.files['file']
            global df
            df=pd.read_csv(file)

            msg="Data Uploaded Succesfully"
            return render_template('upload.html',msg=msg)
        except:
            return render_template('upload.html')
    return render_template('upload.html')
@app.route('/view_data')
def view_data():
    global dataframe
    try:
        dataframe=df.copy()
        dataset=df[:100]

        return render_template('viewdata.html',columns=dataset.columns.values,rows=dataset.values.tolist())
    except NameError:
        return render_template('upload.html')
@app.route('/registration',methods=['POST','GET'])
def registration():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        psw=request.form['password']
        cpsw=request.form['cpassword']

        if psw==cpsw:
            sql='SELECT * from care'
            cur=mydb.cursor()
            cur.execute(sql)
            all_emails=cur.fetchall()
            mydb.commit()
            all_emails=[i[2] for i in all_emails]
            if email in all_emails:
                return render_template('registration.html',msg='a')
            else:
                sql='INSERT INTO care(uname,email,psw) values(%s,%s,%s)'
                values=(name,email,psw)
                cur=mydb.cursor()
                cur.execute(sql,values)
                mydb.commit()
                cur.close()
                return render_template('registration.html',msg='b')
        else:
            return render_template('registration.html',msg='c')
        # else:
        #     for requirement in policy.test_password(psw):
        #         alert = f"{requirement.name} not satisfied: expected: {requirement.requirement}, got: {requirement.actual}"
        #         flash("","success")
        #         return render_template('registration.html',a=alert)


    return render_template('registration.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=="POST":
        email=request.form['email']
        psw=request.form['password']
        session['email']=email
        cursor=mydb.cursor()
        sql='SELECT * FROM care WHERE email=%s and psw=%s'
        val=(session['email'],psw)
        cursor.execute(sql,val)
        results=cursor.fetchall()
        mydb.commit()
        if len(results) >=1:
            return render_template('home.html',msg='Login Successfull')
        else:
            return render_template('login.html',msg='Invalid Credentials')
    return render_template('login.html')
@app.route('/split',methods=['GET','POST'])
def split():
    global X_train,X_test,y_train,y_test

    if request.method=='POST':
        size=int(request.form['split'])
        size=size/100
        dataframe.head()
        data=preprocessing(dataframe)
        data.head()
        a = data.drop(['Stay','case_id','patientid'], axis=1)
        b = data['Stay']
        X_train,X_test,y_train,y_test=train_test_split(a,b,test_size=size,random_state=52)
        print(X_train.columns)
        print(X_train.head())
        return render_template('split.html',msg="Data Preprocessed and Splits Succesfully")
    return render_template('split.html')

@app.route('/model',methods=['GET','POST'])
def model():
    if request.method=='POST':
        algo=request.form['algo']
        if algo=='1':
            model=RandomForestClassifier()
            model.fit(X_train,y_train)
            rpred=model.predict(X_test)
            ac1=accuracy_score(y_test,rpred)
            ac1=ac1*100
            ac1=ac1.round(2)
            return render_template('model.html',msg="Accuracy for SVM is " + str(ac1) +"%")
        elif algo=='2':
            model=KNeighborsClassifier()
            model.fit(X_train, y_train)
            rpred = model.predict(X_test)
            ac2 = accuracy_score(y_test, rpred)
            ac2=ac2*100
            ac2=ac2.round(2)
            return render_template('model.html', msg="Accuracy for KNN is " + str(ac2)+ '%')
        else:
            model=LGBMClassifier()
            model.fit(X_train, y_train)
            rpred = model.predict(X_test)
            ac3 = accuracy_score(y_test, rpred)
            ac3 = ac3 * 100
            ac3 = ac3.round(2)
            return render_template('model.html', msg="Accuracy for LGBM is " + str(ac3)+ '%')




        return render_template('model.html')
    return render_template('model.html')
@app.route('/home')
def home():
    return render_template('home.html')
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/logout')
def logout():
    session.pop('email',None)
    return redirect(url_for('index'))

if __name__=="__main__":
    app.run(debug=True)