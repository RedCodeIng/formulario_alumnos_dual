import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
from datetime import date

def send_confirmation_email(to_email, student_data):
    """
    Sends a confirmation email to the student using HTML template.
    
    Args:
        to_email (str): Recipient email.
        student_data (dict): Dictionary with student info (nombre, matricula, etc.)
    """
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    sender_email = os.environ.get("SMTP_USER", "test@example.com")
    sender_password = os.environ.get("SMTP_PASSWORD", "password")

    today = date.today().strftime("%d/%m/%Y")
    
    # Load HTML Template using Jinja2
    try:
        from jinja2 import Environment, FileSystemLoader
        # Path is currently: src/utils/email_sender.py -> ../templates/email/registro_alumno.html.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(current_dir, "../templates/email")
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("registro_alumno.html")
        html_content = template.render(student_data)
        
    except Exception as e:
        print(f"Error loading template: {e}")
        html_content = f"<p>Hola {student_data.get('nombre_alumno')}, tu registro fue exitoso.</p>"

    subject = "Confirmación de Registro DUAL - Exitoso"

    # Mock Mode Logic
    if sender_email == "test@example.com" or not sender_password:
        print(f"--- [MOCK HTML EMAIL] TO: {to_email} ---")
        print(f"Subject: {subject}")
        # print(html_content) # Too long to print fully
        print("HTML Content generated successfully using template.")
        print("------------------------------------------")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
