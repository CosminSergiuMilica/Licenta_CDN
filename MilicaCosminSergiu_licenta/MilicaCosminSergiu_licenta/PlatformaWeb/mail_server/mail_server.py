import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

SENDER = "milicacosmin1@gmail.com"
PASSWORD = 'ruur vfwu skop bpkm'
recv = 'cosmin-sergiu.milica@student.tuiasi.ro'

app = FastAPI()

def transform_data(data):
    return {
        "domain": data.get("domain"),
        "email": data.get("email")
    }
def send_email(sender_email, password, receiver_email, subject, body):
    smtp_server = "smtp.gmail.com"
    port = 587
    context = ssl.create_default_context()

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls(context=context)  # Activare TLS

        server.login(sender_email, password)

        server.sendmail(sender_email, receiver_email, message.as_string())
    except smtplib.SMTPAuthenticationError as auth_error:

        raise HTTPException(status_code=500,
                            detail="SMTP authentication error. Please check your email address and password.")
    except smtplib.SMTPException as smtp_error:

        raise HTTPException(status_code=500, detail="SMTP error. Please check SMTP server settings.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error sending email.")
    finally:
        server.quit()

@app.post('/api/mail-server/client-origin')
async def send_mail_to_client_origin(request: Request):
    data = await request.json()
    data = transform_data(data)
    sub = "Actualizări importante pentru serverul tău"
    mess = (f"Bună ziua,\n\n"
            f"Sperăm că aveți o zi minunată! Vă contactăm din partea echipei My-CDN pentru a vă informa despre niște actualizări importante legate de serverul dvs. {data['domain']}.\n\n"
            f"Am observat că există mici probleme de conectare, dar nu vă faceți griji, suntem aici să vă ajutăm să le rezolvați cu ușurință!\n\n"
            f"Vă rugăm să verificați situația și să ne anunțați dacă aveți nevoie de asistență suplimentară. Suntem mereu aici pentru a vă ajuta să vă mențineți site-ul online și funcțional.\n\n"
            f"Cu multă considerație,\n"
            f"Echipa My-CDN")

    try:
        send_email(SENDER, PASSWORD, data['email'], sub, mess)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error sending email.")
    return JSONResponse(status_code=200, content={"message": "Mail sent successfully"})

@app.post('/api/mail-server/signup-success')
async def send_mail_signup_succes(request: Request):
    data = await request.json()
    data = transform_data(data)
    sub = "Înregistrare cu succes pe platforma noastră"
    mess = (f"Bună ziua,\n\n"
            f"Vă felicităm pentru înregistrarea cu succes pe platforma noastră! Suntem încântați să vă avem alături și să vă oferim acces la toate serviciile noastre.\n\n"
            f"Dacă aveți întrebări sau aveți nevoie de asistență, nu ezitați să ne contactați. Suntem aici pentru a vă ajuta și pentru a vă asigura că experiența dvs. pe platforma noastră este una plăcută și productivă.\n\n"
            f"Cu sinceritate,\n"
            f"Echipa noastră")

    try:
        send_email(SENDER, PASSWORD, data['email'], sub, mess)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error sending email.")
    return JSONResponse(status_code=200, content={"message": "Mail sent successfully"})

@app.post('/api/mail-server/send-reset-code')
async def sent_reset_code(request: Request):
    data = await request.json()
    email = data.get("email")
    code = data.get("code")
    if not email or not code:
        raise HTTPException(status_code=400, detail='Missing email or code in request')

    sub = "Cod de resetare a parolei"
    mess = f"Bună ziua,\n\nPentru a reseta parola, folosește următorul cod: \n\n** {code} **\n\nCodul este valabil doar 10 minute."
    try:
        send_email(SENDER, PASSWORD, email, sub, mess)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error sending reset code")

    return JSONResponse(status_code=200, content={"message": "Reset code sent successfully"})
def main():
    uvicorn.run("mail_server:app", host="localhost", port=8200, log_level="info")

if __name__ == "__main__":
        main()