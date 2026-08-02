import smtplib
import ssl

# from email import encoders
# from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import utils.credentials as cred

# from utils import config


class Mailer:
    @staticmethod
    def send_report(image_paths: list):
        msg = MIMEMultipart()
        msg['From'] = cred.SENDER_EMAIL
        msg['To'] = cred.RECIPIENT_EMAIL
        msg['Subject'] = "Weekly Energy System Task Report"
        
        body = "Here is this weeks energy task report."
        msg.attach(MIMEText(body, 'plain'))

        for path in image_paths:
            with open(path, "rb") as f:
                # part = MIMEImage(f.read())
                # part.set_param
                # msg.attach(part)
                part = MIMEImage(f.read(),"image/png")
                part.add_header("Content-Disposition", "attachment",filename=path)
                # part.set_param(param="filename",value=path.name)
                # part.add_header("Content-Transfer-Encoding","base64")
                msg.attach(part)
                
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(cred.SMTP_SERVER, cred.SMTP_PORT, context = context) as server:
            server.login(cred.EMAIL_USER, cred.EMAIL_PASSWORD)
            server.send_message(msg)       