# gastos/db.py
from pymongo import MongoClient

# Conexión al servidor de MongoDB
client = MongoClient('mongodb://localhost:27017/') 

# Selecciona la base de datos de tu proyecto
db = client['finanzas_personales']

# Define las colecciones que usarás
usuarios_collection = db['usuarios']
transacciones_collection = db['transacciones']
# ¡Nueva colección para la autenticación!
usuarios_app_collection = db['usuarios_app']