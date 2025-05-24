from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import re
from email_sender import send_verification_code, send_EmailMessages
from datetime import datetime
from sqlalchemy import func
# إعداد التطبيق
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# بيانات الاتصال
username = 'eiadatk'
password = 'o_776039267'
host = 'eiadatk.mysql.pythonanywhere-services.com'
dbname = 'eiadatk$medical_booking'
# إعداد الاتصال
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{username}:{password}@{host}/{dbname}"

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical_booking.db'        # هذه شغلها فقط في حال انك بتشتغل على سيرفر محلي

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------- النماذج --------------------

class District(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hospitals = db.relationship('Hospital', backref='district', lazy=True)

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('district.id'), nullable=False)
    clinics = db.relationship('Clinic', backref='hospital', lazy=True)
    users = db.relationship('User', backref='hospital', lazy=True)
    image_url = db.Column(db.String(255))  # 

class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    capacity = db.Column(db.Integer, default=3)
    doctors = db.relationship('Doctor', backref='clinic', lazy=True)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    otp_code = db.Column(db.String(6), nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    gender = db.Column(db.String(10))
    blood_type = db.Column(db.String(5))
    address = db.Column(db.String(200))
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='patient')
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'))
    appointments = db.relationship('Appointment', backref='user', lazy=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'))  
    period = db.Column(db.String(20), nullable=False)
    attendance_number = db.Column(db.Integer, nullable=False) # رقم الحضور
    status = db.Column(db.String(20), default='pending')

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    blood_type = db.Column(db.String(5))
    address = db.Column(db.String(200))
    clinic_name = db.Column(db.String(100))
    doctor_name = db.Column(db.String(100))
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'))

    hospital = db.relationship('Hospital', backref='patients')

# -------------------- دوال مساعدة --------------------

def verify_otp_code(user_email, user_input_otp):
    user = User.query.filter_by(email=user_email).first()
    stored_otp = user.otp_code
    if stored_otp and stored_otp == user_input_otp:
        user.otp_code = ""
        db.session.commit()
        return True
    return False


# -------------------- المسارات --------------------

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/home')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    districts = District.query.all()
    return render_template('home.html', user=user, districts=districts)

@app.route('/hospitals/<int:district_id>')
def hospitals(district_id):
    hospitals = Hospital.query.filter_by(district_id=district_id).all()
    return render_template('hospitals.html', hospitals=hospitals)

@app.route('/clinics/<int:hospital_id>')
def clinics(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    clinics = Clinic.query.filter_by(hospital_id=hospital_id).all()
    return render_template('clinics.html', clinics=clinics, hospital=hospital)
    
@app.route("/clinic/<int:hospital_id>/add_patient", methods=["POST"])
def add_patient(hospital_id):
    new_patient = Patient(
        name=request.form["patient_name"],
        phone=request.form["patient_phone"],
        gender=request.form["gender"],
        blood_type=request.form["blood_type"],
        address=request.form["address"],
        clinic_name=request.form["clinic_name"],
        doctor_name=request.form["doctor_name"],
        hospital_id=hospital_id  # مهم جدًا
    )
    db.session.add(new_patient)
    db.session.commit()
    return redirect(url_for('hospital_dashboard', hospital_id=hospital_id))


@app.route('/clinics/<int:clinic_id>/doctors')
def doctors(clinic_id):
    clinic = Clinic.query.get_or_404(clinic_id)
    doctors = Doctor.query.filter_by(clinic_id=clinic_id).all()
    return render_template('doctors.html', clinic=clinic, doctors=doctors)


@app.route('/doctors/<int:clinic_id>')
def clinic_doctors(clinic_id):
    clinic = Clinic.query.get_or_404(clinic_id)
    doctors = Doctor.query.filter_by(clinic_id=clinic_id).all()
    return render_template('doctors.html', clinic=clinic, doctors=doctors)


@app.route('/doctor/<int:doctor_id>')
def doctor_info(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    return render_template('doctor_info.html', doctor=doctor)

@app.route('/book/<int:doctor_id>', methods=['GET', 'POST'])
def book(doctor_id):
    print(session)
    if 'user_id' not in session:
        return redirect(url_for('login'))

    doctor = Doctor.query.get_or_404(doctor_id)
    clinic = doctor.clinic
    max_capacity = clinic.capacity
    email = session.get('email')
    user = User.query.filter_by(email=email).first()
    print(doctor, doctor.name)
    if request.method == 'POST':
        selected_date_str = request.form.get('date')
        selected_period = request.form.get('period')

        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
            if selected_date < date.today():
                print("Too old")
                flash("لا يمكن اختيار تاريخ سابق", "danger")
                return redirect(request.url)
        except:
            print("date filed")
            flash("صيغة التاريخ غير صحيحة", "danger")
            return redirect(request.url)

        appointments_count = Appointment.query.join(Doctor).filter(
            Doctor.clinic_id == clinic.id,
            db.func.date(Appointment.date) == selected_date,
            Appointment.period == selected_period
        ).count()

        if appointments_count >= max_capacity:
            print("Too busy")
            flash("الفترة المختارة ممتلئة في هذا التاريخ", "danger")
            return redirect(request.url)

        appointment = Appointment(
            user_id=session['user_id'],
            doctor_id=doctor_id,
            date=datetime.combine(selected_date, datetime.min.time()),
            period=selected_period,
            attendance_number=appointments_count+1
        )
        db.session.add(appointment)
        db.session.commit()

        # جرب تجاهل نتيجة البريد الآن:
        info = f"{doctor.clinic.hospital.name} في عيادة {doctor.clinic.name}/ {doctor.name}"
        send_EmailMessages(user, selected_date, selected_period, info)
        
        flash("تم حجز الموعد بنجاح", "success")
        return redirect(url_for('my_appointments'))


    return render_template('book.html', doctor=doctor)

@app.route('/my_appointments')
def my_appointments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    appointments = Appointment.query.filter_by(user_id=session['user_id']).order_by(Appointment.date.desc()).all()
    return render_template('my_appointments.html', appointments=appointments)

@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    date = appointment.date
    clinic_id = appointment.clinic_id
    period = appointment.period
    
    db.session.delete(appointment)
    db.session.commit()
    
    date_only = date.date()
    start_of_day = datetime.combine(date_only, datetime.min.time())
    end_of_day = datetime.combine(date_only, datetime.max.time())
    
    remaining_appointments = Appointment.query.filter(
        Appointment.clinic_id == clinic_id,
        Appointment.period == period,
        Appointment.date >= start_of_day,
        Appointment.date <= end_of_day
    ).order_by(Appointment.attendance_number).all()
    
    for index, app in enumerate(remaining_appointments, start=1):
        app.attendance_number = index
    
    db.session.commit()
    
    flash("تم إلغاء الحجز وإعادة ترتيب المرضى بنجاح", "success")
    return redirect(url_for('my_appointments'))

@app.route('/hospital_dashboard')
def hospital_dashboard():
    if session.get('role') != 'hospital':
        flash("غير مصرح بالدخول", "danger")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    hospital = Hospital.query.get(user.hospital_id)  #  جلب معلومات المشفى

    patients = User.query.filter_by(hospital_id=user.hospital_id, role='patient').all()
    print(patients, user)
    return render_template('hospital_dashboard.html', patients=patients, hospital=hospital)

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash("غير مصرح بالدخول", "danger")
        return redirect(url_for('login'))
    current_user = User.query.get(session['user_id'])
    users = User.query.filter_by(role='patient').all()
    return render_template('admin_dashboard.html', users=users, current_user=current_user)

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if session.get('role') != 'admin':
        flash("غير مصرح بالدخول", "danger")
        return redirect(url_for('login'))
    user = User.query.get_or_404(user_id)
    if user.role == 'patient':
        db.session.delete(user)
        db.session.commit()
        flash("تم حذف المستخدم بنجاح", "success")
    else:
        flash("لا يمكن حذف هذا المستخدم", "warning")
    return redirect(url_for('admin_dashboard'))

# -------------------- تسجيل حساب جديد --------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        phone = request.form['phone']
        gender = request.form['gender']
        blood_type = request.form['blood_type']
        address = request.form['address']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if len(fullname.split()) < 4:
            flash("الرجاء إدخال الاسم الرباعي", "danger")
            return render_template('register.html')

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash("بريد إلكتروني غير صالح", "danger")
            return render_template('register.html')

        if not phone.startswith(("77", "78", "73", "71", "70")):
            flash("رقم الهاتف غير صالح", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("كلمتا المرور غير متطابقتين", "danger")
            return render_template('register.html')

        if User.query.filter((User.email == email) | (User.phone == phone)).first():
            flash("الحساب موجود مسبقاً", "danger")
            return render_template('register.html')
        
        otp_code = send_verification_code(email) # إرسال كود التحقق عبر البريد الالكتروني وتخزينه في متغير

        if otp_code:
            new_user = User(
                fullname=fullname,
                email=email,
                phone=phone,
                otp_code=otp_code,
                gender=gender,
                blood_type=blood_type,
                address=address,
                password=password  
            )
            session['email'] = email

            db.session.add(new_user)
            db.session.commit()
            flash("تم التسجيل بنجاح", "success")
            return redirect(url_for('verify_otp'))
    # flash("خطأ في ارسال رمز otp", "danger")
    return render_template('register.html')

@app.route('/about')
def about():
    return render_template('tem.html')  # tem.html يجب أن يكون داخل مجلد templates


#######################           الداله حق التحقق ####################3

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        otp = request.form.get('otp')
        email = session.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            verfiy = verify_otp_code(email, otp)

            if verfiy:
                # ✅ توجيه المستخدم حسب دوره
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user.role == 'hospital':
                    return redirect(url_for('hospital_dashboard'))
                else:
                    return redirect(url_for('index'))  # للمستخدم العادي
            else:
                flash('رمز التحقق غير صحيح', 'danger')
    return render_template('verify_otp.html')



@app.route('/login', methods=['GET', 'POST'])    # هذا  حق التحقق
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        session['email'] = email
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['temp_user_id'] = user.id
            session['temp_role'] = user.role
            
            # بدل إنشاء رمز التحقق الحقيقي فقط عطيه رقم ثابت أو عشوائي بدون إرسال
            otp_code = send_verification_code(user.email)  # رمز ثابت للتجربة
            user.otp_code = otp_code
            db.session.commit()
            
            
            
            return redirect(url_for('verify_otp'))
        else:
            flash("الحساب أو كلمة المرور غير صحيحة", "danger")
    return render_template('login.html')

##############3 ------------------------###########################3333

@app.route('/logout')
def logout():
    session.clear()
    flash("تم تسجيل الخروج بنجاح", "success")
    return redirect(url_for('login'))

#########################################################################
def init_db_data():
    db.drop_all()
    db.create_all()

    # إضافة المدير العام (أدمن)
    admin = User(
        fullname="المدير العام",
        email="admenuser23@gmail.com",
        phone="781918261",
        gender="ذكر",
        blood_type="O+",
        address="المدينة الرئيسية",
        password="Adminuser555",
        role="admin"
    )
    db.session.add(admin)

    # إضافة المديريات
    d1 = District(name=" المكلا")
    db.session.add_all([d1])
    db.session.commit()

    h1 = Hospital(
    name="مستوصف الحياة",
    district=d1,
    image_url="img/1.jpeg"
)

    h2 = Hospital(
    name="مستشفى العرب",
    district=d1,
    image_url="img/2.png"
)

    h3 = Hospital(
    name="مركز طب الأسرة",
    district=d1,
    image_url="img/hospital3.jpg"
)

    db.session.add_all([h1, h2, h3])
    db.session.commit()


    # إضافة العيادات
    ##################                  H1 ######################################
    c1 = Clinic(name=" الجراحه العامه", hospital=h1)

    c4 = Clinic(name=" اذن وانف وحنجرة", hospital=h1)

    c7 = Clinic(name=" امراض جلديه وتناسليه وتجميل", hospital=h1)

############################     H2         ###############################
    c2 = Clinic(name=" امراض صدريه وتنفسيه", hospital=h2)

    c5 = Clinic(name="  امراض باطنه وقلب", hospital=h2)

    c8 = Clinic(name=" اخصائي امراض  المخ والاعصاب", hospital=h2)

    c10 = Clinic(name=" نساء وتوليد", hospital=h2)

    c12 = Clinic( name="  اخصائي جراجه ومناظير الكلى والمسالك البوليه والضعف الجنسي والعقم , البورد العربي"  , hospital=h2)

    #######################          H3           ########################

    c3 = Clinic(name="عيادة الأسنان", hospital=h3)

    c6 = Clinic(name="عيادة النساء والتوليد", hospital=h3)

    c9 = Clinic(name="عيادة الأطفال", hospital=h3)

    c11 = Clinic(name="عيادة الباطنية", hospital=h3)


    db.session.add_all([c1, c2, c3, c4,c5,c6,c7,c8,c9,c10,c11 ,c12])
    db.session.commit()

    # إضافة الأطباء

    ########################################   H1 ########################################

    doc1 = Doctor(name=" د.  مهدي سالم مرعي ", specialty="جراحه عامه", clinic=c1)  

    doc4 = Doctor(name="د.  حسين ابوبكر بن قاسم باعشن", specialty=" اذن وانف وحنجرة" , clinic=c4)

    doc7 = Doctor(name="د. ايمن عمر باضروس ", specialty="امراض جلديه وتناسليه وتجميل", clinic=c7)


########################################   H2 ########################################

    doc2 = Doctor(name="د.  عصام علي ميهوب", specialty="امراض صدريه وتنفسيه", clinic=c2)

    doc5 = Doctor(name=" د. سميرة عوض بانصر   ", specialty=" امراض باطنه وقلب", clinic=c5)

    doc8 = Doctor(name=" د.  إبراهيم محمد فروح ", specialty="اخصائي امراض المخ والاعصاب", clinic=c8)

    doc10 = Doctor(name="د.  نسيبة ابراهيم محمد اسماعيل", specialty="نساء وتوليد", clinic=c10)

    doc12 = Doctor(name="د. لطفي احمد سالم  البوري", specialty="  اخصائي جراجه ومناظير الكلى والمسالك البوليه والضعف الجنسي والعقم , البورد العربي", clinic=c12)


########################################   H3 ########################################

    doc3 = Doctor(name="د. أحمد اليماني", specialty="أسنان", clinic=c3)   
    doc6 = Doctor(name="د. ليلى العمري", specialty="نساء وتوليد", clinic=c6)
    doc9 = Doctor(name="د. سامي الشامي", specialty="أطفال", clinic=c9)
    doc11 = Doctor(name="د. مريم الخطيب", specialty="باطنية", clinic=c11)

    db.session.add_all([doc1, doc2,doc3, doc4,doc5,doc6,doc9,doc11,doc7,doc8,doc10, doc12])      
    db.session.commit()

    # إضافة حساب مستشفى (مدير مستشفى)
    hospital_user1 = User(
        fullname="مدير مستوصف الحياة ",
        email="binmelhi@gmail.com",
        phone="711560711",
        gender="ذكر",
        blood_type="A+",
        address="المكلا",
        password="hospitalpass1400",
        role="hospital",
        hospital=h1
    )

    # hospital_user2 = User(
    #     fullname="مدير مستشفى العرب ",
    #     email="hospital2@example.com",
    #     phone="99887766",
    #     gender="ذكر",
    #     blood_type="A+",
    #     address="المكلا",
    #     password="hospitalpass1300",
    #     role="hospital",
    #     hospital=h2
    # )

    # hospital_user3 = User(
    #     fullname="مدير مستشفى مركز طب الاسره ",
    #     email="hospital3@example.com",
    #     phone="99887766",
    #     gender="ذكر",
    #     blood_type="A+",
    #     address="المكلا",
    #     password="hospitalpass1200",
    #     role="hospital",
    #     hospital=h3
    # )

    db.session.add(hospital_user1)
    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        init_db_data()
    app.run(debug=True)

