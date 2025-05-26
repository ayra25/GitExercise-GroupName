from flask_mail import Message
from flask import current_app
from extensions import mail  

def send_reset_email(to_email, reset_link):
    msg = Message('Password Reset Request',
                  recipients=[to_email])
    msg.body = f'''
    Hi,

    To reset your password, click the link below:
    {reset_link}

    If you didn’t request this, please ignore this email.

    Thanks,
    MMUnity
    '''
    mail.send(msg)
