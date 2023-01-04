import math
from gettext import install
from sre_constants import FAILURE
from tokenize import Double
from flask import make_response
import hashlib
import sqlalchemy
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum
from datetime import *

#-------------------------------------------------------------
# VARIABILI GLOBALI CHE PERMETTONO DI CONNETTERSI AL DATABASE 
# Se si necessita di cambiare la modalità di connessione basta
# modificare il contenuto di queste due variabili
address = "localhost"
port = "3306"
database = "fitems"
session = None
# per il locale usa '127.0.0.1:3306', 'fitems'
#-------------------------------------------------------------

Base = declarative_base()

# definito un tipo enumerativo per la gestione dei casi che possono verificarsi quando
# viene eseguita una query: può avere successo, può fallire o l'elemento può già esistere 
# (vedere ad esempio il caso degli utenti)
class Return(Enum):
    SUCCESS = 1
    FAILURE = 2
    EXISTS = 3


# DEFINIZIONE DELLE CLASSI CHE VANNO A RAPPRESENTARE LE TABELLE DEL DB
# Per ciascuna viene anche implementato il metodo di pretty-printing a scopo di sviluppo
# +----
class Utente(Base):
    __tablename__ = "Utente"
    
    username = Column(String, primary_key = True)
    nome = Column(String)
    cognome = Column(String)
    email = Column(String)
    data = Column(Date)
    password_hash = Column(String)
    longitudine = Column(Float)
    latitudine = Column(Float)
    
    def __repr__(self):
        return "<Utente (username: %s, nome: %s, congome: %s)>" % (self.username, self.nome, self.cognome)

    def _asdict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}

    
class Post(Base):
    __tablename__ = 'Post'
    
    id_post = Column(Integer, primary_key = True)
    titolo = Column(String)
    descrizione = Column(String)
    stato = Column(Integer)
    data = Column(Date)
    username = Column(String)
    image_path = Column(String)
    
    def __repr__(self):
        return "<Corso (titolo: %s, descrizione: %s, utente: %s)>" % (self.titolo, self.descrizione, self.username)
    
    def _asdict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}

class Messaggio(Base):
    __tablename__ = 'Messaggio'
    
    id_messaggio = Column(Integer, primary_key = True)
    mittente = Column(String)
    destinatario = Column(String)
    contenuto = Column(String)
    time = Column(Date)
    visualizzato = Column(Integer)
    
    def __repr__(self):
        return "<Corso (mittente: %s, destinatario: %s, contenuto: %s)>" % (self.mittente, self.destinatario, self.contenuto)
    
    def _asdict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}

# + - - - - - - - - - - +
# |  METODI DI APPOGGIO |
# + - - - - - - - - - - +

def initialize_connection ():
    try:
        engine = create_engine('mysql+pymysql://admin:yQ9q8XgWYzYQv3RWccc3'+'@' + address+':'+ port + '/' + database)

        maker = sessionmaker(bind = engine)
        global session
        session = maker()
        return Return.SUCCESS
    except:
        print("[*] - Errore nella creazione della sessione")
        return Return.FAILURE

def check_connection():
    if(session == None):
        return initialize_connection() 

    return Return.SUCCESS

def make_dictonary(query):
    return  query._asdict()

def make_list_of_dictonary(query,nameOfList):
    diz = dict()
    i = 0
    lista = []
    for u in query:
        i = i + 1
        lista.append(u._asdict())
    diz['nResults'] = i
    diz[nameOfList] = lista
    return diz

def does_user_exist(username):
    check_connection()
    if(session.query(Utente).filter(Utente.username == username).count() > 0):
        return 1
    else:
        return 0

# + - - - - - - - - - - +
# |        METODI       |
# + - - - - - - - - - - +


#---- Metodo utile per verificare le credenziali fornite in fase di accesso e quindi per stabilire
#     se l'utente può avere accesso all'area privata del sito
def check_user_login(username, password):
    check_connection()
    if(username != None and password != None and username != '' and password != ''):
        # genero l'hash della nuova password e poi comparo gli hash
        passwordHash = hashlib.sha256(password.encode()).hexdigest()
        if(session.query(Utente).filter(Utente.username == username).filter(Utente.password_hash == passwordHash).count() > 0):
            return Return.SUCCESS

    return Return.FAILURE

#---- Metodo che esegue una query per ottenere le informazioni personali di un utente specifico
def get_user_info(username):
    check_connection()
    info = make_dictonary(session.query(Utente.username, Utente.nome, Utente.cognome, Utente.email, Utente.latitudine, Utente.longitudine, Utente.data).filter(Utente.username == username).one())
    info['postPubblicati'] = session.query(Post.username).filter(Post.username == username).group_by(Post.username).count()
    return info

#---- Metodo che per aggiornare le info personali di un utente
def update_user_info(username,nome,cognome,email,latitudine,longitudine,data):
    if(check_connection() == Return.FAILURE): return Return.FAILURE
    try:
        query = session.query(Utente).filter(Utente.username == username)
        if(nome != None and nome != ''):
            query.update({'nome': nome})
        if(cognome != None and cognome != ''):
            query.update({'cognome': cognome})
        if(email != None and email != ''):
            query.update({'email': cognome})
        if(latitudine != None and latitudine != ''):
            query.update({'latitudine': latitudine})
        if(longitudine != None and longitudine != ''):
            query.update({'longitudine': longitudine})
        if(data != None and data != ''):
            query.update({'data': data})
        session.commit()
        return Return.SUCCESS
    except Exception as e:
        print("[!] - Errore nell'aggiornamento dei dati personali!\n" +
              "      Vedi metodo update_user_info()\n" +
              "      Per maggiori info:\n")
        print(e)
        return Return.FAILURE

#---- Metodo utilizzato per inserire un nuovo utente nella base di dati
def register_user(username, nome, cognome, email, password, latitudine, longitudine, data):
    if(check_connection() == Return.FAILURE): return Return.FAILURE
    try:
        # genero l'hash della nuova password
        passwordHash = hashlib.sha256(password.encode()).hexdigest()
        # creo il nuovo oggetto da inserire nella tabella utenti
        new_utente = Utente(username = username, nome = nome, cognome = cognome, email = email,
                            password_hash = passwordHash, latitudine = latitudine, longitudine = longitudine, data = data)
        
        # controllo anche a mano se è già presente l'utente che si vuole inserire in modo 
        # da ritornare il tipo di ritorno EXISTS
        if (does_user_exist(username)):
            return Return.EXISTS
        
        # se l'utente non è già presente aggiungo alla base di dati ed eseguo subito un commit
        # per riflettere l'operazione: operazione necessaria per fare in modo che successivamente
        # si sia in grado di trovare la chiave all'interno dei tipi specializzati docenti e partecipanti
        session.add(new_utente)
        session.commit()
        
        # se arrivo qui vuol dire che tutti gli inserimenti sono avvenuti con successo
        return Return.SUCCESS
    except Exception as e:
        print("[!] - Utente già presente nella base di dati o errore nell'inserimento!\n" +
              "      Vedi metodo insert_new_user()\n" +
              "      Per maggiori info:\n")
        print(e)
        return Return.FAILURE

def create_new_post(titolo,descrizione,username):
    if(check_connection() == Return.FAILURE): return Return.FAILURE
    try:
        data = datetime.today().strftime('%Y-%m-%d')
        new_post = Post(titolo = titolo, descrizione = descrizione, username = username, data = data, stato = 0)
        session.add(new_post)
        session.commit()
        return Return.SUCCESS
    except Exception as e:
        print("[!] - Errore nella creazione di un nuovo post!\n" +
              "      Vedi metodo create_new_user()\n" +
              "      Per maggiori info:\n")
        print(e)
        return Return.FAILURE

def create_new_message(mittente,destinatario,contenuto):
    if(check_connection() == Return.FAILURE): return Return.FAILURE
    try:
        time = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        new_message = Messaggio(contenuto = contenuto, mittente = mittente, destinatario = destinatario, time = time, visualizzato = 0)
        session.add(new_message)
        session.commit()
        return Return.SUCCESS
    except Exception as e:
        print("[!] - Errore nella creazione di un nuovo messaggio!\n" +
              "      Vedi metodo create_new_message()\n" +
              "      Per maggiori info:\n")
        print(e)
        return Return.FAILURE

def get_post(limit, latitude, longitude):

    if(check_connection() == Return.FAILURE): return Return.FAILURE
    radius = 500
    # se l'utente non ha settato un limite o il limite è troppo grande lo imposto a 20
    if( limit == None or int(limit) > 50):
        limit = 20
    else:
        limit = int(limit)

    try:
        # se ha settato un limite in base alla posizione ritorno i risultati filtrati per distanza
        if(latitude != None and longitude != None):
            min_lat  = float(latitude) - (float(radius) / 6378000) * (180 / 3.141592)
            max_lat  = float(latitude) + (float(radius) / 6378000) * (180 / 3.141592)
            min_long = float(longitude) - (float(radius) / 6378000) * (180 / 3.141592) / math.cos(float(latitude) * 3.141592/180)
            max_long = float(longitude) + (float(radius) / 6378000) * (180 / 3.141592) / math.cos(float(latitude) * 3.141592/180)
            return make_list_of_dictonary(session.query(Post).filter(Utente.username == Post.username).filter(
                                          Utente.latitudine.between(min_lat,max_lat)).filter(
                                          Utente.longitudine.between(min_long,max_long)).limit(limit).all(), "post")
    
        # altrimenti non filtro in base alla posizione gps
        return make_list_of_dictonary(session.query(Post).limit(limit).all(),"post")

    except Exception as e:
        print("[!] - Errore nel caricamento dei post!\n" +
              "      Vedi metodo get_post()\n" +
              "      Per maggiori info:\n")
        print(e)
        return Return.FAILURE

def get_post_by_id(idPost):

    if(check_connection() == Return.FAILURE): return Return.FAILURE
    try:
        return make_dictonary(session.query(Post).filter(Post.id_post == idPost).one())
    except Exception as e:
        print("[!] - Errore nel caricamento del post!\n" +
              "      Vedi metodo get_post()\n" +
              "      Per maggiori info:\n")
        print(e)
        return Return.FAILURE

def get_chats(username):
    if(check_connection() == Return.FAILURE): return Return.FAILURE
    try:
        return make_list_of_dictonary(session.query(Utente.username
                            ).filter(or_(Utente.username == Messaggio.mittente, Utente.username == Messaggio.destinatario)
                            ).filter(Utente.username != username).all(),"chats")
    except Exception as e:
        print("[!] - Errore nel caricamento delle chat!\n" +
              "      Vedi metodo get_chats()\n" +
              "      Per maggiori info:\n")
        print(e)
        return Return.FAILURE

def get_chat(username1, username2, limit):
    if(check_connection() == Return.FAILURE): return Return.FAILURE
    if( limit == None or int(limit) > 100):
        limit = 20
    try:
        return make_list_of_dictonary(session.query(Messaggio
                                     ).filter(or_(and_(username1 == Messaggio.mittente, username2 == Messaggio.destinatario), 
                                                  and_(username2 == Messaggio.mittente, username1 == Messaggio.destinatario))
                                     ).order_by(Messaggio.time.desc()).limit(limit).all(),"chat")
    except Exception as e:
        print("[!] - Errore nel caricamento della chat!\n" +
              "      Vedi metodo get_chat()\n" +
              "      Per maggiori info:\n")
        print(e)
        return Return.FAILURE

def visualizza_messaggi(destinatario,mittente):
    if(check_connection() == Return.FAILURE): return Return.FAILURE
    try:
        session.query(Messaggio).filter(Messaggio.destinatario == destinatario
                            ).filter(Messaggio.mittente == mittente
                            ).filter(Messaggio.visualizzato == 0).update({'visualizzato': 1})
        session.commit()
    except Exception as e:
        print("[!] - Errore nella visualizzazione!\n" +
              "      Vedi metodo visualizza_messaggi()\n" +
              "      Per maggiori info:\n")
        print(e)
        return Return.FAILURE

def add_image_path(idPost, path):
    if(check_connection() == Return.FAILURE): return Return.FAILURE
    try:
        session.query(Post).filter(Post.id_post == idPost).update({'image_path':path})
        session.commit()

    except Exception as e:
        print("[!] - Errore nel caricamento della image_path nel DB!\n" +
              "      Vedi metodo add_image_path()\n" +
              "      Per maggiori info:\n")
        print(e)
        return Return.FAILURE

