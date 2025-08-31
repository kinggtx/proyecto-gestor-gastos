# gastos/views.py
from django.shortcuts import render, redirect
from django.urls import reverse
from .db import usuarios_app_collection, usuarios_collection, transacciones_collection
from django.contrib.auth.hashers import make_password, check_password
from bson.objectid import ObjectId
from datetime import datetime # Importar el módulo datetime

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

def crear_perfil(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre_perfil')
        ingreso_mensual = request.POST.get('ingreso_mensual')

        # Validación de datos (simple)
        if not nombre or not ingreso_mensual:
            return render(request, 'crear_perfil.html', {
                'error': 'Ambos campos son obligatorios.'
            })

        # Crea el documento para MongoDB
        perfil_documento = {
            'nombre_perfil': nombre,
            'ingreso_mensual_estimado': float(ingreso_mensual)
        }

        # Inserta el documento en la colección de usuarios
        usuarios_collection.insert_one(perfil_documento)

        # Redirige a la siguiente página (por ahora, al mismo formulario)
        # En el futuro, podrías redirigir a la página de inicio o a la lista de gastos
        return redirect('crear_perfil')

    # Si es una solicitud GET, simplemente muestra el formulario
    return render(request, 'crear_perfil.html')

def dashboard(request):
    if 'user_id' not in request.session:
        return redirect('login')

    user_id = ObjectId(request.session['user_id'])

    # Obtener la información del perfil del usuario
    perfil = usuarios_collection.find_one({'_id': user_id})

    # Obtener las transacciones del usuario
    transacciones = list(transacciones_collection.find({'usuario_id': user_id}).sort('fecha', -1)) # Ordenar por fecha descendente

    # Lógica de cálculo
    total_ingresos = 0
    total_gastos = 0
    gastos_por_categoria = {}

    for t in transacciones:
        t['fecha_str'] = t['fecha'].strftime('%Y-%m-%d') # Formatear la fecha para la plantilla
        if t['tipo'] == 'ingreso':
            total_ingresos += t['monto']
        else:
            total_gastos += t['monto']
            categoria = t.get('categoria', 'Sin Categoría')
            gastos_por_categoria[categoria] = gastos_por_categoria.get(categoria, 0) + t['monto']

    balance_actual = total_ingresos - total_gastos
    ahorro_actual = balance_actual # Ahorro es simplemente el balance, ya que no hay una cuenta de "ahorros" separada

    context = {
        'perfil': perfil,
        'transacciones': transacciones,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'balance_actual': balance_actual,
        'gastos_por_categoria': gastos_por_categoria,
        'ahorro_actual': ahorro_actual,
    }

    return render(request, 'dashboard.html', context)