
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import time

class EmailService:
    def __init__(self, sender_email: str, app_password: str):
        self.sender_email = sender_email
        self.app_password = app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    def send_single(self, to: str, subject: str, body: str, html: bool = False):
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html' if html else 'plain'))
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.app_password)
            server.send_message(msg)
    
    def send_bulk(self, recipients: List[dict], subject: str, body_template: str, html: bool = False):
        """
        recipients: [{"email": "a@x.com", "name": "Alice"}, ...]
        body_template: "Hello {name}, your interview is scheduled."
        """
        results = {"success": [], "failed": []}
        
        # If no recipients, return empty results
        if not recipients:
            return results
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                
                for recipient in recipients:
                    email = recipient.get('email')
                    if not email:
                        continue
                        
                    try:
                        # Simple format if keys exist in template, otherwise safe format or just body
                        try:
                            personalized_body = body_template.format(**recipient)
                        except KeyError:
                            # If template expects specific keys not present, fall back to original body
                            personalized_body = body_template
                            
                        msg = MIMEMultipart()
                        msg['From'] = self.sender_email
                        msg['To'] = email
                        msg['Subject'] = subject
                        msg.attach(MIMEText(personalized_body, 'html' if html else 'plain'))
                        
                        server.send_message(msg)
                        results["success"].append({"email": email, "status": "sent"})
                        
                        time.sleep(0.5)  # Rate limiting
                        
                    except Exception as e:
                        results["failed"].append({"email": email, "status": "failed", "error": str(e)})
        except Exception as e:
             # If connection fails completely
             # Mark all as failed or return global error
             for r in recipients:
                 results["failed"].append({"email": r.get('email'), "status": "failed", "error": f"Connection Error: {str(e)}"})
        
        return results
