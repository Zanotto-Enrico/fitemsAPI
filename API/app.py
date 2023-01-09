from flask import Flask, flash, request, redirect, url_for, send_from_directory
from database import *
from flask import request
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = './pictures'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "JG{~^VQnAX8dK*4P'=/XTg^rBhH_psx+/zK9#>YkR_bWd7Av"
session = dict()


@app.route('/')
def index():
	info = "<h2> /register per registrare un nuovo utente (POST)</h2>" 
	info += "<h4> Passare username, password, nome, cognome, data (intesa come nascita), email, latitudine, longitudine (in decimale) facendo un POST alla pagina </h4> /register</br></br>"
	info += "<h2> /login per eseguire il login e aprire una sessione (POST)</h2>" 
	info += "<h4> Passare username e password facendo un POST alla pagina </h4> /login</br></br>"
	info += "<h2> /myInfo per listare le mie info personali (GET) (DEVI ESSERE LOGGATO) </h2> "
	info += "<h4> Questa chiamata non ha parametri</h4> /myInfo</br></br>"
	info += "<h2> /myInfo per aggiornare le mie info personali (POST) (DEVI ESSERE LOGGATO) </h2> "
	info += "<h4> Passare i parametri che si vole aggiornare scegliendo un insieme tra i seguenti: nome, cognome,data (nascita), email,latitudine, longitudine (in decimale) facendo un POST alla pagina </h4> /myInfo</br></br>"
	info += "<h2> /post per elencare i post (GET)</h2> </br>"
	info += "<h4> Per settare un limite massimo di post elencati</h4> /post?limite=3 </br></br>"
	info += "<h4> Per settare un filtro basato sulla posizione gps fornire le coordinate in decimale</h4>/post?latitudine=45.1234567&longitudine=13.1234567</br></br>"
	info += "<h2> /myposts per ottenere tutti i propri post (GET) (DEVI ESSERE LOGGATO) </h2> "
	info += "<h4> Questa chiamata non ha parametri</h4> /myposts</br></br>"
	info += "<h2> /makepost per creare un nuovo post (POST) (DEVI ESSERE LOGGATO)</h2>" 
	info += "<h4> Passare titolo, descrizione, facendo un POST alla pagina </h4> /makepost</br></br>"
	info += "<h2> /itemfound per chiudere un post aperto (POST) (DEVI ESSERE LOGGATO)</h2>" 
	info += "<h4> Passare postId e username (di chi lo ha trovato, opzionale), facendo un POST alla pagina </h4> /itemfound</br></br>"
	info += "<h2> /sendmessage per inviare un messaggio (POST) (DEVI ESSERE LOGGATO)</h2>" 
	info += "<h4> Passare destinatario, contenuto, facendo un POST alla pagina </h4> /sendmessage</br></br>"
	info += "<h2> /mychats per elencare le mie chat attive (GET) (DEVI ESSERE LOGGATO)</h2> </br>"
	info += "<h4> Questa chiamata non ha parametri</h4> /mychats</br></br>"
	info += "<h2> /chat elencare gli ultimi n messaggi di una chat (GET) (DEVI ESSERE LOGGATO)</h2> </br>"
	info += "<h4> Passare obbligatoriamente utente (l'altro utente nella chat oltre a te)</h4> /mychats?utente=mario97</br></br>"
	info += "<h4> Passare opzionalmente limite (un limite massimo di messaggi)(vale 20 di default)</h4> /mychats?utente=mario97&limite=10</br></br>"
	info += "<h2> /visualizza marcare i messaggi di una chat come 'visualizzati' (POST) (DEVI ESSERE LOGGATO)</h2>" 
	info += "<h4> Passare mittente(il mittente dei messaggi) facendo un POST alla pagina </h4> /visualizza</br></br>"
	info += "<h2> /uploadImage aggiornare la foto di un post (POST) (DEVI ESSERE LOGGATO)</h2>" 
	info += "<h4> Passare un multipart/form-data contenente l'immagine e l'idPost facendo un POST alla pagina </h4> /uploadImage</br></br>"
	info += "<h2> /getImage per ottenere l'immagine di un post (GET)</h2> </br>"
	info += "<h4> Passare come parametro l'idPost del post voluto</h4> /getImage?idPost=1 </br></br>"
	
	
	return info

@app.route('/myInfo', methods=['GET','POST'])
def utenti():
	if "user" not in session:
		return response('FAILURE')
	if request.method == 'GET':
		return get_user_info(session['user'])
	if request.method == 'POST':
		ret = update_user_info(session['user'],request.form.get('nome'), request.form.get('cognome'),request.form.get('email'), request.form.get('latitudine'), request.form.get('longitudine'), request.form.get('data'))
		if(ret == Return.SUCCESS):
			return response('SUCCESS')
	return response('FAILURE')

@app.route('/myposts', methods=['GET'])
def myposts():
	if "user" not in session:
		return response('FAILURE')
	return get_post(username=session['user'], limit=100)

@app.route('/post', methods=['GET'])
def post():
	limit = request.args.get('limite')
	longitude = request.args.get('longitudine')
	latitude = request.args.get('latitudine')
	return get_post(limit,latitude,longitude)

@app.route('/register', methods=['POST'])
def register():
	ret = register_user(request.form.get('username'),request.form.get('nome'),request.form.get('cognome'),
						request.form.get('email'),request.form.get('password'),
						request.form.get('latitudine'),request.form.get('longitudine'),
						request.form.get('data'))
	if(ret == Return.SUCCESS):
		return response('SUCCESS')
	elif(ret == Return.EXISTS):
		return response('EXIST')
	else:
		return response('FAILURE' )

@app.route('/login', methods=['POST'])
def login():
	if(check_user_login(request.form.get('username'),request.form.get('password')) == Return.SUCCESS):
		session["user"] = request.form.get("username")
		return response('LOGGED IN')
	if(check_user_login(request.args.get('username'),request.args.get('password')) == Return.SUCCESS):
		session["user"] = request.form.get("username")
		return response('LOGGED IN')
	return response('ERROR')

@app.route('/makepost', methods=['POST'])
def makepost():
	if "user" not in session:
		return response('FAILURE')

	ret = create_new_post(request.form.get('titolo'),request.form.get('descrizione'),session["user"])
	if(ret == Return.SUCCESS):
		return response('SUCCESS')
	else:
		return response('FAILURE' )

@app.route('/itemfound', methods=['POST'])
def itemFound():
    if "user" in session:
        ret = closePost(request.form.get('postId'),session['user'],request.form.get('username'))
        if(ret == Return.SUCCESS):
            return response('SUCCESS')
    return response('FAILURE')

@app.route('/sendmessage', methods=['POST'])
def makemessage():
	if "user" not in session:
		return response('FAILURE')

	ret = create_new_message(session["user"], request.form.get('destinatario'), request.form.get('contenuto'))
	if(ret == Return.SUCCESS):
		return response('SUCCESS')
	else:
		return response('FAILURE' )

@app.route('/mychats', methods=['GET'])
def mychats():
	if "user" not in session:
		return response('FAILURE')
	return get_chats(session["user"])

@app.route('/chat', methods=['GET'])
def chat():
	if "user" not in session:
		return response('FAILURE')
	if request.args.get('utente') == None:
		return response('FAILURE')
	return get_chat(session["user"],request.args.get('utente'), request.args.get('limite'))

@app.route('/visualizza', methods=['POST'])
def visualizza():
	if "user" not in session:
		return response('FAILURE')
	if request.form.get('mittente') == None:
		return response('FAILURE')

	visualizza_messaggi(session["user"],request.form.get('mittente'))
	return response('SUCCESS')

@app.route('/uploadImage', methods=['POST'])
def uploadImage():
	if "user" not in session:
		return response('FAILURE')
	if request.form.get('idPost') == None:
		return response('FAILURE')

	if not request.files:
		return response("FAILURE")

	file = request.files['immagine']
	if file.filename == '':
		return response("FAILURE")
		
	if file and allowed_file(file.filename):
		post = get_post_by_id(request.form.get('idPost'))
		filename = "post_" + str(post[1]['id_post'])+'.'+file.filename.rsplit('.', 1)[1].lower()
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		add_image_path(idPost= request.form.get('idPost'), path="pictures/"+filename)
		return response("SUCCESS")
	return response("FAILURE")



@app.route('/getImage', methods=['GET'])
def getImage():
	if request.args.get('idPost') == None:
		return response('FAILURE')
	idPost = request.args.get('idPost')
	for i in ALLOWED_EXTENSIONS:
		if(os.path.exists("pictures/post_"+idPost+"."+i)):
			return send_from_directory(app.config["UPLOAD_FOLDER"], "post_"+idPost+"."+i)
	return response("NO FILE FOUND")
		


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def response(message):
	print({"status":message})
	return {"status":message}
