import smtplib

s = smtplib.SMTP('smtp.gmail.com', 587)

s.starttls()

s.login("sender_email_id", "sender_email_id_password")

message = "Message_you_need_to_send"
# we can handle this by the use of cookies
s.sendmail("<sender_mail_id>", "<receiver_mail_id>", message)
s.quit()
