import smtplib


def mail_me(user_mail, pro_mess):
	mail_ref = smtplib.SMTP('smtp.gmail.com', 587)
	mail_ref.starttls()
	mail_ref.login("vivek16csu427@ncuindia.edu", "VivekChoudhary@2898")
	message = pro_mess
	# we can handle this by the use of cookies
	mail_ref.sendmail("vivek16csu427@ncuindia.edu", user_mail, message)
	mail_ref.quit()
