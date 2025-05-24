import random
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# إعداد الحساب
EMAIL_SENDER = "eiadatk2@gmail.com"
EMAIL_PASSWORD = "sngi rvkl hbea xguh"

# ارسال رمز otp عبر البريد الالكتروني للمستخدم عند تسجيل الدخول
def send_verification_code(user_email: str):
    otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

    subject = "رمز التحقق الخاص بك"
    body = f"رمز التحقق لتسجيل الدخول هو: {otp_code}"

    msg = EmailMessage()
    msg['From'] = EMAIL_SENDER
    msg['To'] = user_email
    msg['Subject'] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return otp_code
    except:
        return ""
    

#! اشعار المستخدم بقبول طلبه وتحديد موعد حجزه
def send_EmailMessages(user, date, period, info, type: str = "confirm"):
    name = user.fullname # user`s name from database
    user_email = user.email

    # عنوان الرسالة ومحتوياتها
    if type == "confirm":
        subject = "لقد تم حجز موعدك بنجاح"
        body = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.8; direction: rtl; background-color: #f9f9f9; padding: 20px; color: #333;">
    
    <h2 style="color: #007BFF;">تأكيد الموعد</h2>
    <p>مرحبًا <strong>{name}</strong>،</p>
    <p>لقد تم حجز موعدك بنجاح في <strong>{info}</strong>.</p>

    <h3 style="color: #555;">تفاصيل الموعد</h3>
    <p>
      <strong>التاريخ:</strong> {date} <br>
      <strong>الفترة:</strong> {period}
    </p>

    <h3 style="color: #555;">ملاحظات مهمة</h3>
    <p>
      نرجو <u>الالتزام بالحضور</u> في الوقت المحدد ونرجو لكم الشفاء العاجل.<br>
      للاطلاع على موقع العيادة، يرجى زيارة:
      <a href="https://eiadatk.com" style="color: #007BFF;">رابط الصفحة بالنقر هنا</a>
    </p>

    <p>
      شكرًا لاستخدامك منصة
      <span style="color: #007BFF; font-size: 22px; font-weight: bold;">عيادتك</span>
    </p>

  </body>
</html>
"""
    elif type == "alret":
        subject = "تنبيه: دورك عند الطبيب اقترب – لم يتبقَ سوى 4 أشخاص فقط!"
        body = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.8; direction: rtl; background-color: #f9f9f9; padding: 20px; color: #333;">

    <h2 style="color: #e63946;">🔔 تنبيه هام بخصوص موعدك</h2>

    <p>عزيزي <strong>{name}</strong>،</p>

    <p>
      نود إعلامك بأن موعد دخولك إلى الطبيب الذي قمت بالحجز لديه قد اقترب.
      لم يتبقَ أمامك سوى <strong style="color: #e63946; font-size: 18px;">أربعة أشخاص فقط</strong>!
    </p>

    <h3 style="color: #555;">تفاصيل الموعد</h3>
    <p>
      <strong>العيادة:</strong> {info} <br>
      <strong>التاريخ:</strong> {date} <br>
      <strong>الفترة:</strong> {period}
    </p>

    <p style="margin-top: 20px;">
      نرجو <u>الاستعداد والتوجه إلى العيادة</u> في أقرب وقت ممكن لتجنب التأخير.
    </p>

    <p>
      شكرًا لاستخدامك منصة
      <span style="color: #007BFF; font-size: 22px; font-weight: bold;">عيادتك</span>
    </p>

  </body>
</html>
"""
        
    # إعداد الرسالة
    msg = MIMEMultipart("alternative")
    msg['From'] = EMAIL_SENDER
    msg['To'] = user_email
    msg['Subject'] = subject

    # دمج محتوى HTML
    html_part = MIMEText(body, "html")
    msg.attach(html_part)

    # ارسال البريد الى ايميل المستخدم
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_SENDER, user_email, msg.as_string())

        return True
    except:
        return False
    
