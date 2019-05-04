import smtplib


def mail_me(user_mail, pro_mess):
	mail_ref = smtplib.SMTP('smtp.gmail.com', 587)
	mail_ref.starttls()
	mail_ref.login("sender_email_id", "sender_email_id_password")
	message = pro_mess
	# we can handle this by the use of cookies
	mail_ref.sendmail("<sender_mail_id>", user_mail, message)
	mail_ref.quit()
