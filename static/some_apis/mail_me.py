import smtplib


def mail_me(user_mail, pro_mess):
	mail_ref = smtplib.SMTP('smtp.gmail.com', 587)
	mail_ref.starttls()
	mail_ref.login("<senders_email>", "<senders_password>")
	message = pro_mess
	# we can handle this by the use of cookies
	mail_ref.sendmail("<senders_email>", user_mail, message)
	mail_ref.quit()
