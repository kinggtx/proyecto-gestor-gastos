# gastos/views.py
from django.shortcuts import render, redirect
from django.urls import reverse
from .db import usuarios_app_collection, usuarios_collection, transacciones_collection
from django.contrib.auth.hashers import make_password, check_password
from bson.objectid import ObjectId
from datetime import datetime # Importar el módulo datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from collections import defaultdict # Para el desglose de gastos

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        nombre_perfil = request.POST.get('nombre_perfil')
        ingreso_mensual = request.POST.get('ingreso_mensual')

        if not all([username, password, nombre_perfil, ingreso_mensual]):
            return render(request, 'register.html', {
                'error': 'Todos los campos son obligatorios.'
            })

        # Verificar si el usuario ya existe
        if usuarios_app_collection.find_one({'username': username}):
            return render(request, 'register.html', {
                'error': 'El nombre de usuario ya existe.'
            })

        # Hashear la contraseña
        hashed_password = make_password(password)

        # Crear el documento del usuario de autenticación
        usuario_doc = usuarios_app_collection.insert_one({
            'username': username,
            'password': hashed_password,
        })
        
        # Obtener el ID del usuario recién creado
        user_id = usuario_doc.inserted_id

        # Crear el documento del perfil personal con el mismo ID
        perfil_doc = {
            '_id': user_id,
            'nombre_perfil': nombre_perfil,
            'ingreso_mensual_estimado': float(ingreso_mensual)
        }
        usuarios_collection.insert_one(perfil_doc)
        
        return redirect('login')
    
    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Busca el usuario en MongoDB
        user = usuarios_app_collection.find_one({'username': username})

        # Verifica si el usuario existe y si la contraseña es correcta
        if user and check_password(password, user['password']):
            request.session['user_id'] = str(user['_id'])
            request.session['username'] = user['username']
            return redirect('dashboard') # ¡Redirección al panel de control!
        else:
            return render(request, 'login.html', {'error': 'Usuario o contraseña incorrectos.'})


    return render(request, 'login.html')

def logout_view(request):
    request.session.flush() # Elimina todos los datos de la sesión
    return redirect('login')


def dashboard(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    user_id = ObjectId(request.session['user_id'])
    perfil = usuarios_collection.find_one({'_id': user_id})
    transacciones = list(transacciones_collection.find({'usuario_id': user_id}).sort('fecha', -1))
    
    total_ingresos = 0
    total_gastos = 0
    gastos_por_categoria = defaultdict(float)
    
    gastos_por_mes = defaultdict(float)
    ingresos_por_mes = defaultdict(float)
    
    hoy = datetime.now()
    mes_actual = hoy.strftime('%Y-%m')
    
    for t in transacciones:
        # Aquí está la corrección: crea un atributo 'id_str' sin guion bajo.
        t['id_str'] = str(t['_id']) 
        t['fecha_str'] = t['fecha'].strftime('%Y-%m-%d')
        mes_transaccion = t['fecha'].strftime('%Y-%m')

        if t['tipo'] == 'ingreso':
            total_ingresos += t['monto']
            ingresos_por_mes[mes_transaccion] += t['monto']
        else:
            total_gastos += t['monto']
            categoria = t.get('categoria', 'Sin Categoría')
            gastos_por_categoria[categoria] += t['monto']
            gastos_por_mes[mes_transaccion] += t['monto']
            
    balance_actual = total_ingresos - total_gastos
    
    labels_categorias = list(gastos_por_categoria.keys())
    data_categorias = list(gastos_por_categoria.values())

    fechas_unicas = sorted(list(set(list(gastos_por_mes.keys()) + list(ingresos_por_mes.keys()))), reverse=True)
    
    fechas_grafico = fechas_unicas[:6]
    fechas_grafico.reverse()
    
    gastos_grafico = [gastos_por_mes.get(mes, 0) for mes in fechas_grafico]
    ingresos_grafico = [ingresos_por_mes.get(mes, 0) for mes in fechas_grafico]
    
    context = {
        'perfil': perfil,
        'transacciones': transacciones,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'balance_actual': balance_actual,
        'labels_categorias': labels_categorias,
        'data_categorias': data_categorias,
        'labels_meses': fechas_grafico,
        'data_gastos_mensuales': gastos_grafico,
        'data_ingresos_mensuales': ingresos_grafico,
    }
    return render(request, 'dashboard.html', context)



@csrf_exempt
@require_POST
def add_transaction(request):
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'No autorizado'}, status=401)

    try:
        data = json.loads(request.body)
        user_id = ObjectId(request.session['user_id'])

        new_transaction = {
            'usuario_id': user_id,
            'tipo': data['tipo'],
            'monto': float(data['monto']),
            'descripcion': data.get('descripcion', ''),
            'categoria': data.get('categoria', 'Sin Categoría'),
            'fecha': datetime.now()
        }
        transacciones_collection.insert_one(new_transaction)

        return JsonResponse({'success': True, 'message': 'Transacción agregada con éxito'})

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)