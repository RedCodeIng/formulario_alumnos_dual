
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def send_confirmation_email(to_email, student_data):
    """
    Sends a confirmation email to the student using HTML template.
    
    Args:
        to_email (str): Recipient email.
        student_data (dict): Dictionary with student info (nombre, matricula, etc.)
    """
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    sender_email = os.environ.get("SMTP_EMAIL", "test@example.com")
    sender_password = os.environ.get("SMTP_PASSWORD", "password")

    today = date.today().strftime("%d/%m/%Y")
    
    # Load HTML Template
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, "../assets/email_template.html")
        with open(template_path, "r", encoding="utf-8") as f:
             html_content = f.read()
             
        # Replacements
        html_content = html_content.replace("{{nombre}}", student_data.get("nombre", "Alumno"))
        html_content = html_content.replace("{{matricula}}", student_data.get("matricula", "N/A"))
        html_content = html_content.replace("{{carrera}}", student_data.get("carrera", "ISC"))
        html_content = html_content.replace("{{proyecto}}", student_data.get("proyecto", "Proyecto DUAL"))
        html_content = html_content.replace("{{empresa}}", student_data.get("ue", "Empresa"))
        html_content = html_content.replace("{{periodo}}", student_data.get("fecha_inicio", today)) # Placeholder
        html_content = html_content.replace("{{link_acceso}}", "http://localhost:8502") # Access Link
        
    except Exception as e:
        print(f"Error loading template: {e}")
        html_content = f"<p>Hola {student_data.get('nombre')}, tu registro fue exitoso.</p>"

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
