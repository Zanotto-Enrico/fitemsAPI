from flask import Flask
from database import *
from flask import request


app = Flask(__name__)
app.secret_key = "JG{~^VQnAX8dK*4P'=/XTg^rBhH_psx+/zK9#>YkR_bWd7Av"
session = dict()

@app.route('/')
def index():
	info = "<h2>/utenti per listare gli utenti (GET)     (da rimuovere)</h2> </br></br>"
	info += "<h2> /register per registrare un nuovo utente (POST)</h2>" 
	info += "<h4> Passare username, nome, cognome,email, data (intesa come data di nascita),latitudine, longitudine (in decimale) facendo un POST alla pagina </h4> /register</br></br>"
	info += "<h2> /login per eseguire il login e aprire una sessione (POST)</h2>" 
	info += "<h4> Passare username e password facendo un POST alla pagina </h4> /login</br></br>"
	info += "<h2> /post per elencare i post (GET)</h2> </br>"
	info += "<h4> Per settare un limite massimo di post elencati</h4> /post?limite=3 </br></br>"
	info += "<h4> Per settare un filtro basato sulla posizione gps fornire le coordinate in decimale</h4>/post?latitudine=45.1234567&longitudine=13.1234567</br></br>"
	info += "<h2> /makepost per creare un nuovo post (POST) (DEVI ESSERE LOGGATO)</h2>" 
	info += "<h4> Passare titolo, descrizione, facendo un POST alla pagina </h4> /makepost</br></br>"
	info += "<h2> /sendmessage per inviare un messaggio (POST) (DEVI ESSERE LOGGATO)</h2>" 
	info += "<h4> Passare destinatario, contenuto, facendo un POST alla pagina </h4> /sendmessage</br></br>"
	info += "<h2> /mychats per elencare le mie chat attive (GET) (DEVI ESSERE LOGGATO)</h2> </br>"
	info += "<h4> Questa chiamata non ha parametri</h4> /mychats</br></br>"
	info += "<h2> /chat elencare gli ultimi n messaggi di una chat (GET) (DEVI ESSERE LOGGATO)</h2> </br>"
	info += "<h4> Passare obbligatoriamente utente (l'altro utente nella chat oltre a te)</h4> /mychats?utente=mario97</br></br>"
	info += "<h4> Passare opzionalmente limite (un limite massimo di messaggi)(vale 20 di default)</h4> /mychats?utente=mario97&limite=10</br></br>"
	info += "<h2> /visualizza marcare i messaggi di una chat come 'visualizzati' (POST) (DEVI ESSERE LOGGATO)</h2>" 
	info += "<h4> Passare mittente(il mittente dei messaggi) facendo un POST alla pagina </h4> /visualizza</br></br>"
	return info

@app.route('/utenti', methods=['GET'])
def utenti():
	return get_users()

@app.route('/post', methods=['GET'])
def post():
	limit = request.args.get('limite')
	longitude = request.args.get('longitudine')
	latitude = request.args.get('latitudine')
	return get_post(limit,latitude,longitude)

@app.route('/register', methods=['POST'])
def register():
	ret = register_user(request.form.get('username'),request.form.get('nome'),request.form.get('cognome'),
						request.form.get('email'),request.form.get('data'),request.form.get('password'),
						request.form.get('latitudine'),request.form.get('longitudine'))
	if(ret == Return.SUCCESS):
		return 'SUCCESS'
	elif(ret == Return.EXISTS):
		return 'EXIST'
	else:
		return 'FAILURE' 

@app.route('/login', methods=['POST'])
def login():
	if(check_user_login(request.form.get('username'),request.form.get('password')) == Return.SUCCESS):
		session["user"] = request.form.get("username")
		return 'LOGGED IN'
	return 'ERROR'

@app.route('/makepost', methods=['POST'])
def makepost():
	if "user" not in session:
		return 'FAILURE'

	ret = create_new_post(request.form.get('titolo'),request.form.get('descrizione'),session["user"])
	if(ret == Return.SUCCESS):
		return 'SUCCESS'
	else:
		return 'FAILURE' 

@app.route('/sendmessage', methods=['POST'])
def makemessage():
	if "user" not in session:
		return 'FAILURE'

	ret = create_new_message(session["user"], request.form.get('destinatario'), request.form.get('contenuto'))
	if(ret == Return.SUCCESS):
		return 'SUCCESS'
	else:
		return 'FAILURE' 

@app.route('/mychats', methods=['GET'])
def mychats():
	if "user" not in session:
		return 'FAILURE'
	return get_chats(session["user"])

@app.route('/chat', methods=['GET'])
def chat():
	if "user" not in session:
		return 'FAILURE'
	if request.args.get('utente') == None:
		return 'FAILURE'
	return get_chat(session["user"],request.args.get('utente'), request.args.get('limite'))

@app.route('/visualizza', methods=['POST'])
def visualizza():
	if "user" not in session:
		return 'FAILURE'
	if request.form.get('mittente') == None:
		return 'FAILURE'

	visualizza_messaggi(session["user"],request.form.get('mittente'))
	return 'SUCCESS'