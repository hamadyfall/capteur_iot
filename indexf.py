import time, serial, json
import firebase_admin
from firebase_admin import credentials, db

# --- CONFIGURATION FIREBASE ---
CERT_PATH = "serviceAccountKey.json"  # Le fichier téléchargé à l'étape 1
DB_URL = "https://capteur-iot-default-rtdb.europe-west1.firebasedatabase.app/" # Votre URL Firebase

cred = credentials.Certificate(CERT_PATH)
firebase_admin.initialize_app(cred, {'databaseURL': DB_URL})

# Référence vers l'emplacement des données
ref = db.reference('capteurs/sol')

# --- CONFIGURATION SÉRIE ---
PORT = "/dev/tty.usbserial-1420"
ser = serial.Serial(PORT, 9600, timeout=2)
CMD = bytes.fromhex("010300000008440C")

print("Connecté à Firebase")


def lire_et_envoyer():
    ser.write(CMD)
    res = ser.read(25)
    if len(res) >= 21:
        payload = {
            "timestamp": int(time.time()),
            "humidite": int.from_bytes(res[3:5], "big") / 10,
            "temp": int.from_bytes(res[5:7], "big") / 10,
            "ec": int.from_bytes(res[7:9], "big"),
            "ph": int.from_bytes(res[9:11], "big") / 10,
            "N": int.from_bytes(res[11:13], "big"),
            "P": int.from_bytes(res[13:15], "big"),
            "K": int.from_bytes(res[15:17], "big"),
            "fertilite": int.from_bytes(res[17:19], "big")
        }

        try:
            # .push() crée un identifiant unique automatique pour chaque envoi
            ref.push(payload)
            print(f"Envoyé à Firebase ! {payload['temp']}°C")
        except Exception as e:
            print(f"Erreur Firebase : {e}")
    else:
        print(f"Réponse incomplète : {len(res)} octets")


try:
    while True:
        lire_et_envoyer()
        time.sleep(60)
except KeyboardInterrupt:
    ser.close()
    print("Arrêt propre.")
