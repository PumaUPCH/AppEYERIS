import flet as ft
from flet import AppBar, Image, Row, Dropdown, TextField, TextButton,ElevatedButton,Stack, Page, Text, View,Container, ListView,Column,Divider,Container
import psycopg2
import pyrebase
import requests  # Necesario para descargar la imagen
import openpyxl
import shutil
import os
import boto3
from io import BytesIO
from botocore.exceptions import NoCredentialsError, ClientError

s3_client = boto3.client('s3')
bucket_name = 'reporte-pacientes'
plantilla_excel_key = 'Plantilla_Final.xlsx'

DB_URL="postgresql://root:f0IIV5sVGMalJpeOrNaoy0HwmqIOgN4E@dpg-cspoaaggph6c73do4qjg-a.oregon-postgres.render.com/datos_pacientes"

ruta_logo = "https://res.cloudinary.com/dmknonkwh/image/upload/v1731347609/zuazmrkt0vr6zwzlqctd.png"
ruta_imagen_doctor = "https://res.cloudinary.com/dmknonkwh/image/upload/v1731347868/xpaaazaw9k5xljbnkuxz.png"
ruta_imagen_semicirculo = "https://res.cloudinary.com/dmknonkwh/image/upload/v1731348165/bafs8tpelvbohobirjrz.png"

nombre_doc_global=""
apellidoP_doc_global=""
apellidoM_doc_global=""
cmp_doc_global=""

# Conectar a la base de datos PostgreSQL
def conectar_db():
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def obtener_pacientes():
    conn = conectar_db()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, apellido_paterno, apellido_materno, dni FROM pacientes")
            pacientes = cursor.fetchall()
            cursor.close()
            conn.close()
            return pacientes
        except Exception as e:
            print(f"Error al consultar la base de datos: {e}")
            return []
    else:
        return []

# Consultar los resultados de un paciente específico
def obtener_resultados_paciente(paciente_id):
    conn = conectar_db()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nombre, apellido_paterno, apellido_materno, dni, telefono, sexo, edad, motivo_consulta, antecedentes_medicos, 
                       clasificacion, confiabilidad, vcdr, url_imagen_original, url_imagen_segmentada, id, fecha 
                FROM pacientes 
                WHERE id = %s
            """, (paciente_id,))
            paciente = cursor.fetchone()
            cursor.close()
            conn.close()
            return paciente
        except Exception as e:
            print(f"Error al consultar los resultados del paciente: {e}")
            return None
    else:
        return None

firebaseConfig = {
    "apiKey": "AIzaSyB8nCoidFKJv9krwoBbzwIF_ObU3xedwqs",
    "authDomain": "cuentas-doc.firebaseapp.com",
    "projectId": "cuentas-doc",
    "storageBucket": "cuentas-doc.firebasestorage.app",
    "messagingSenderId": "976170484572",
    "appId": "1:976170484572:web:b5a14faef0029c185b3799",
    "measurementId": "G-6XF2442F78",
    "databaseURL": ""  # Deja vacío si no usas Realtime Database
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

def main(page: ft.Page):
    page.title = "Aplicación EYERIS"
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = True
    page.bgcolor = "#64dcb3"

    def change_route(e,ruta,paciente_id=None):
        if ruta == "/inicio":
            page.views.append(inicio())
        elif ruta=="/inicio_sesion_previo":
            page.views.append(inicio_sesion_previo())
        elif ruta=="/create_account":
            page.views.append(create_account())
        elif ruta == "/inicio_sesion":
            page.views.append(inicio_sesion())
        elif ruta == "/lista_pacientes":
            page.views.append(lista_pacientes_view())
        elif ruta == "/detalle_paciente" and paciente_id is not None:
            page.views.append(detalle_paciente_view(paciente_id))
        elif ruta == "/mensaje_doc" and paciente_id is not None:
            page.views.append(enviar_mensaje(paciente_id))
        elif ruta == "/reporte_pacientes":
             # Ajusta el tamaño de la ventana para una computadora cuando entres a la vista de reporte de pacientes
            page.window.width = 1024
            page.window.height = 768
            page.window.resizable = True  # Permitir redimensionamiento en la vista de computadora
            page.views.append(reporte_pacientes())
            
        page.update()

    # ESTRUCTURA DE LA FUNCIÓN DE INICIO DE SESIÓN Y REGISTRO DE CUENTA
    def inicio():
        page.controls.clear()

        email=TextField(width=280,height=40,hint_text='Correo electrónico',border='underline',color='black',prefix_icon=ft.icons.EMAIL,)
        password=TextField(width=280,height=40,hint_text='Contraseña',border='underline',color='black',prefix_icon=ft.icons.LOCK,password=True,)
        boton_doc_tec=Dropdown(label="Seleccione el método de ingreso", 
                     options=[
                         ft.dropdown.Option("Doctor","Doctor"),
                         ft.dropdown.Option("Personal de salud","Personal de salud"),
                     ])

        def login_action(e):
            email_value = email.value
            password_value = password.value
            try:
                user = auth.sign_in_with_email_and_password(email_value, password_value)
                user_info = auth.get_account_info(user['idToken'])
                email_verified = user_info['users'][0]['emailVerified']

                if email_verified:
                    if boton_doc_tec.value == "Doctor":
                        change_route(e, "/inicio_sesion")
                    elif boton_doc_tec.value == "Personal de salud":
                        change_route(e, "/inicio_sesion_previo")
                    else:
                        # Mostrar mensaje si no se seleccionó ninguna opción
                        page.snack_bar = ft.SnackBar(ft.Text("Por favor, selecciona una opción válida."))
                        page.snack_bar.open = True
                        page.update()
                else:
                    page.snack_bar = ft.SnackBar(ft.Text("Por favor, verifica tu correo antes de iniciar sesión."))
                    page.snack_bar.open = True
                    page.update()
            except Exception as ex:
                error_snackbar = ft.SnackBar(ft.Text("Error de inicio de sesión: " + str(ex)), open=True)
                page.overlay.append(error_snackbar)
                page.update()
            
        login_button=ElevatedButton(content=ft.Text('INICIAR', color='white', weight='w500'),width=280,bgcolor='black',on_click=login_action)
        create_account_button=TextButton("Crear una cuenta",on_click=lambda e: change_route(e,'/create_account'))

        
        body = ft.Container(
            ft.Row([
                ft.Container(
                    ft.Column(controls=[
                        ft.Container(
                            content=Image(src=ruta_logo, width=200, height=200),
                            alignment=ft.alignment.center,
                            padding=ft.padding.only(top=10, bottom=20)
                        ),
                        ft.Text(
                            'Iniciar Sesión',
                            width=360,
                            size=30,
                            weight='w900',
                            text_align='center'
                        ),
                        ft.Container(email, padding=ft.padding.only(20, 10)),
                        ft.Container(password, padding=ft.padding.only(20, 10)),
                        ft.Container(boton_doc_tec,padding=ft.padding.only(20,10)),
                        ft.Container(login_button, padding=ft.padding.only(25, 10)),
                        ft.Container(
                            ft.Row([
                                ft.Text('¿No tiene una cuenta?'),
                                create_account_button
                            ], spacing=8),
                            padding=ft.padding.only(40)
                        ),
                    ],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    ),
                    gradient=ft.LinearGradient(['blue', 'cyan']),
                    width=360,
                    height=800,
                    border_radius=10
                ),
            ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            ),
            padding=10,
        )
        return View("/inicio", [body])
    
    def create_account():
        page.controls.clear()

        new_email=TextField(width=280,height=40,hint_text='Nuevo correo electrónico',border='underline',color='black',prefix_icon=ft.icons.EMAIL,)
        new_password=TextField(width=280,height=40,hint_text='Nueva contraseña',border='underline',color='black',prefix_icon=ft.icons.LOCK,password=True,)
        confirm_password=TextField(width=280,height=40,hint_text='Confirmar contraseña',border='underline',color='black',prefix_icon=ft.icons.LOCK,password=True,)
        boton_doc_tec=Dropdown(label="Seleccione el método de ingreso", 
                     options=[
                         ft.dropdown.Option("Doctor","Doctor"),
                         ft.dropdown.Option("Personal de salud","Personal de salud"),
                     ])

        def register_action(e):
            email_value = new_email.value
            password_value = new_password.value
            confirm_password_value = confirm_password.value

            if password_value != confirm_password_value:
                error_snackbar = ft.SnackBar(ft.Text("Las contraseñas no coinciden"), open=True)
                page.overlay.append(error_snackbar)
                page.update()
            else:
                try:
                    user = auth.create_user_with_email_and_password(email_value, password_value)
                    # Aquí puedes agregar lógica adicional, como almacenar más datos en Firestore
                    auth.send_email_verification(user['idToken'])
                    page.snack_bar = ft.SnackBar(ft.Text("Registro exitoso. Verifica tu correo para activar tu cuenta."))
                    page.snack_bar.open = True
                    page.update()
                    change_route(e, "/inicio")  # Redirigir a inicio de sesión
                except Exception as ex:
                    error_snackbar = ft.SnackBar(ft.Text("Error al registrarse: " + str(ex)), open=True)
                    page.overlay.append(error_snackbar)
                    page.update()

        register_button=ElevatedButton(content=ft.Text('REGISTRARME', color='white', weight='w500'),width=280,bgcolor='black',on_click=register_action)

        body = ft.Container(
            ft.Row([
                ft.Container(
                    ft.Column(controls=[
                        # Logo e título
                        ft.Container(
                            content=Image(src=ruta_logo, width=200, height=200),
                            alignment=ft.alignment.center,
                            padding=ft.padding.only(top=10, bottom=20)
                        ),
                        ft.Text(
                            'Crear Cuenta',
                            width=360,
                            size=30,
                            weight='w900',
                            text_align='center'
                        ),
                        # Campos de texto y botones
                        ft.Container(new_email, padding=ft.padding.only(20, 10)),
                        ft.Container(new_password, padding=ft.padding.only(20, 10)),
                        ft.Container(confirm_password, padding=ft.padding.only(20, 10)),
                        ft.Container(boton_doc_tec, padding=ft.padding.only(20, 10)),
                        ft.Container(register_button, padding=ft.padding.only(25, 10)),
                        # Botón para redirigir a inicio de sesión
                        ft.Container(
                            ft.TextButton(
                                "¿Ya tienes una cuenta? Inicia sesión",
                                on_click=lambda e: change_route(e, '/inicio')
                            ),
                            padding=ft.padding.only(40)
                        )
                    ],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    ),
                    gradient=ft.LinearGradient(['red', 'orange']),
                    width=360,
                    height=800,
                    border_radius=10
                ),
            ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            ),
            padding=10,
        )
        return View("/register_account", [body])
    
    #PANTALLA INICIO PARA DOCTOR
    def inicio_sesion():
        # Definir los campos de texto
        nombre_doc = TextField(label="Nombre", bgcolor="#f7bf70", color="#000002", border_radius=20)
        apellidoP_doc = TextField(label="Apellido Paterno", bgcolor="#f7bf70", color="#000002", border_radius=20)
        apellidoM_doc = TextField(label="Apellido Materno", bgcolor="#f7bf70", color="#000002", border_radius=20)
        cmp_doc = TextField(label="CMP", bgcolor="#f7bf70", color="#000002", border_radius=20)

        # Función para guardar datos del doctor
        def guardar_datos_doctor(e):
            global nombre_doc_global, apellidoP_doc_global, apellidoM_doc_global, cmp_doc_global
            nombre_doc_global = nombre_doc.value
            apellidoP_doc_global = apellidoP_doc.value
            apellidoM_doc_global = apellidoM_doc.value
            cmp_doc_global = cmp_doc.value
            change_route(e, "/lista_pacientes")

        # Botones
        save_button = ElevatedButton("Iniciar sesión", on_click=guardar_datos_doctor, bgcolor="#c6d8e3", color="#020202")

        # Título
        titulo = Container(
            content=Text(
                "Inicio de sesión",
                size=30,  # Tamaño del texto
                weight="bold",  # Texto en negrita
                color="#000000",  # Color del texto
            ),
            bgcolor="#e8eaf6",  # Color de fondo del título
            border_radius=10,  # Esquinas redondeadas
            padding=10,  # Espaciado alrededor del texto
            alignment=ft.alignment.center,  # Alineación centrada
        )

        # Imagen en la parte inferior de la ventana
        imagen_inferior = Container(
            content=Image(src="https://drive.google.com/uc?export=view&id=1gYvaNUgfV8b2RQLUSIvl53aQoRsjkfFe", fit="contain"),
            alignment=ft.alignment.bottom_center,
            expand=True  # Asegura que la imagen ocupe el ancho completo
        )

        # Imagen de doctores
        imagen_doctores = Container(
            content=Image(src="https://drive.google.com/uc?export=view&id=1mISwx_pP2vUS6cTs1AbAljDihxIcZiJf", fit="contain"),
            alignment=ft.alignment.bottom_center,
            expand=True  # Asegura que la imagen ocupe el ancho completo
        )

        # Contenedor principal para toda la vista
        main_container = Container(
            content=Stack(  # Usamos Stack para superponer el contenido y la imagen
                controls=[
                    imagen_inferior,  # Imagen en el fondo
                    imagen_doctores,  # Imagen encima de la anterior
                    Column(
                        [
                            titulo,
                            nombre_doc,
                            apellidoP_doc,
                            apellidoM_doc,
                            cmp_doc,
                            Row([save_button], alignment=ft.MainAxisAlignment.CENTER)  # Añade espaciamiento entre los botones
                        ],
                        spacing=20,  # Espacio entre cada elemento del Column
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    ),
                ],
            ),
            bgcolor="#d1d2db",  # Color de fondo de la vista
            padding=30,  # Padding alrededor del contenido
            expand=True
        )

        return View("/inicio_sesion", [main_container])
    
    def lista_pacientes_view():
        pacientes = obtener_pacientes()
        lista_pacientes = ft.ListView(expand=True, spacing=10, padding=10)

        if pacientes:
            for paciente in pacientes:
                paciente_id = paciente[0]
                nombre_completo = f"{paciente[1]} {paciente[2]} {paciente[3]}"
                dni = paciente[4]

                ver_detalle_button = ft.ElevatedButton(
                    f"Ver detalles de {nombre_completo}",
                    on_click=lambda e, id=paciente_id: change_route(e, "/detalle_paciente", paciente_id=id),
                    bgcolor="#c6d8e3", color="#020202"
                )

                lista_pacientes.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"Nombre: {nombre_completo}"),
                            ft.Text(f"DNI: {dni}"),
                            ver_detalle_button,
                            ft.Divider()
                        ])
                    )
                )
        else:
            lista_pacientes.controls.append(ft.Text("No se encontraron pacientes."))

        return ft.View("/lista_pacientes", [
            ft.AppBar(title=ft.Text("Lista de Pacientes")),
            lista_pacientes,
            ft.ElevatedButton("Volver al inicio", on_click=lambda e: change_route(e, "/inicio_sesion"), bgcolor="#c6d8e3", color="#020202")
        ])
    
    def detalle_paciente_view(paciente_id):
        paciente = obtener_resultados_paciente(paciente_id)

        if paciente:
            nombre_completo = f"{paciente[0]} {paciente[1]} {paciente[2]}"
            dni = paciente[3]
            telefono = paciente[4]
            sexo = paciente[5]
            edad = paciente[6]
            motivo = paciente[7]
            antecedentes = paciente[8]
            clasificacion = paciente[9]
            confiabilidad = f"Confiabilidad de resultados: {paciente[10]:.2f}"
            vcdr = f"Relación Copa/Disco: {paciente[11]:.2f}"
            url_img_original = paciente[12]
            url_img_fusionada = paciente[13]

            def visualizar_img_orig(e):
                page.launch_url(url_img_original)

            def visualizar_img_seg(e):
                page.launch_url(url_img_fusionada)

            img_orig_button=ft.ElevatedButton("Imagen original",on_click=visualizar_img_orig, bgcolor="#c6d8e3", color="#020202")
            img_seg_button=ft.ElevatedButton("Imagen segmentada",on_click=visualizar_img_seg, bgcolor="#c6d8e3", color="#020202")

            enviar_comentario_button = ft.ElevatedButton("Enviar mensaje", on_click=lambda e: change_route(e, "/mensaje_doc", paciente_id=paciente_id), bgcolor="#c6d8e3", color="#020202")
            volver_lista_button = ft.ElevatedButton("Lista de pacientes", on_click=lambda e: change_route(e, "/lista_pacientes"), bgcolor="#c6d8e3", color="#020202")

            return ft.View("/detalle_paciente", [
                ft.AppBar(title=ft.Text(f"Detalles del Paciente: {nombre_completo}")),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Nombre: {nombre_completo}"),
                        ft.Text(f"DNI: {dni}"),
                        ft.Text(f"Teléfono: {telefono}"),
                        ft.Text(f"Sexo: {sexo}"),
                        ft.Text(f"Edad: {edad}"),
                        ft.Text(f"Motivo: {motivo}"),
                        ft.Text(f"Antecedentes: {antecedentes}"),
                        ft.Text(f"Clasificación: {clasificacion}"),
                        ft.Text(confiabilidad),
                        ft.Text(vcdr),
                        ft.Divider(),
                        ft.Row([ft.Text("Imagen Original:"), ft.Text("Imagen Segmentada:")], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Row([ft.Image(src=url_img_original, width=150, height=150), ft.Image(src=url_img_fusionada, width=150, height=150)], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Row([img_orig_button,img_seg_button], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(),
                        ft.Row([enviar_comentario_button, volver_lista_button], alignment=ft.MainAxisAlignment.CENTER)
                    ])
                )
            ])
        else:
            return ft.View("/detalle_paciente", [
                ft.Text("No se encontraron los detalles del paciente."),
                ft.ElevatedButton("Regresar a la Lista de Pacientes", on_click=lambda e: change_route(e, "/lista_pacientes"), bgcolor="#c6d8e3", color="#020202")
            ])
        
    def enviar_mensaje(paciente_id):
        mensaje_doc = ft.TextField(label="Mensaje de retroalimentación", multiline=True,width=400,height=250)
        paciente = obtener_resultados_paciente(paciente_id)

        # Utilizar los datos del doctor almacenados durante el inicio de sesión
        nombre_doc = nombre_doc_global
        apellidoP_doc = apellidoP_doc_global
        apellidoM_doc = apellidoM_doc_global
        cmp_doc = cmp_doc_global

        generar_reporte_button = ElevatedButton(
            "Generar Reporte", 
            on_click=lambda e: generar_reporte(
                paciente, 
                nombre_doc, 
                apellidoP_doc, 
                apellidoM_doc, 
                cmp_doc, 
                mensaje_doc.value
            ),bgcolor="#c6d8e3", color="#020202"
        )
        volver_detalle_button = ElevatedButton("Volver a Detalles", on_click=lambda e: change_route(e, "/detalle_paciente", paciente_id),bgcolor="#c6d8e3", color="#020202")
        volver_button = ElevatedButton("Volver a la lista de pacientes", on_click=lambda e: change_route(e, "/lista_pacientes"),bgcolor="#c6d8e3", color="#020202")

        return View(
            "/mensaje_doc",
            [
                # Container que centra la Column tanto vertical como horizontalmente
                Container(
                    content=Column(
                        [
                            Text("Ingresar mensaje de retroalimentación", size=20),
                            mensaje_doc,
                            Row(
                                [generar_reporte_button, volver_detalle_button],
                                alignment=ft.MainAxisAlignment.CENTER
                            ),
                            Row(
                                [volver_button],
                                alignment=ft.MainAxisAlignment.CENTER
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    alignment=ft.alignment.center,  # Centrado horizontal y vertical
                    expand=True  # Hace que el contenedor ocupe todo el espacio de la pantalla
                )
            ]
        )
    
    def generar_reporte(paciente,nombre_doc,apellidoP_doc,apellidoM_doc,cmp_doc,mensaje_doc):
        plantilla_stream = BytesIO()
        s3_client.download_fileobj(bucket_name, plantilla_excel_key, plantilla_stream)
        plantilla_stream.seek(0)

        # Crear una copia de la plantilla en memoria
        wb = openpyxl.load_workbook(plantilla_stream)
        hoja = wb.active

        hoja["A6"]=paciente[0]
        hoja["C6"]=paciente[1]
        hoja["E6"]=paciente[2]
        hoja["B4"]=paciente[3]
        hoja["D3"]=paciente[5]
        hoja["D4"]=paciente[4]
        hoja["F3"]=paciente[6]
        hoja["A9"]=paciente[7]
        hoja["A12"]=paciente[8]
        hoja["D16"]=paciente[9]
        hoja["D17"]=paciente[11]
        hoja["G1"]=paciente[14]
        hoja["F4"]=paciente[15]

        hoja["B20"]=nombre_doc
        hoja["B21"]=apellidoP_doc
        hoja["B22"]=apellidoM_doc
        hoja["B23"]=cmp_doc
        hoja["E20"]=mensaje_doc

        # Manejo de imágenes
        try:
            img_url = paciente[12]
            img_url_seg = paciente[13]

            if img_url:
                response = requests.get(img_url, stream=True)
                if response.status_code == 200:
                    img_data = BytesIO(response.content)
                    img = openpyxl.drawing.image.Image(img_data)
                    img.width, img.height = 150, 150
                    img.anchor = "A15"
                    hoja.add_image(img)

            if img_url_seg:
                response_seg = requests.get(img_url_seg, stream=True)
                if response_seg.status_code == 200:
                    img_seg_data = BytesIO(response_seg.content)
                    img_seg = openpyxl.drawing.image.Image(img_seg_data)
                    img_seg.width, img_seg.height = 150, 150
                    img_seg.anchor = "D15"
                    hoja.add_image(img_seg)
        except Exception as e:
            print(f"Error al procesar imágenes: {e}")

        # Guardar el archivo en un stream de bytes
        nuevo_excel_stream = BytesIO()
        wb.save(nuevo_excel_stream)
        nuevo_excel_stream.seek(0)

        # Subir el archivo a S3 con el nombre basado en el DNI del paciente
        try:
            nombre_archivo_s3 = f"{paciente[3]}.xlsx"  # DNI como nombre
            s3_client.upload_fileobj(
                nuevo_excel_stream, bucket_name, nombre_archivo_s3,
                ExtraArgs={'ContentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}
            )
            print(f"Reporte subido exitosamente a S3: {nombre_archivo_s3}")
        except Exception as e:
            print(f"Error al subir archivo a S3: {e}")

        # Notificar al usuario
        page.dialog = ft.AlertDialog(title=Text(f"Reporte subido a S3 como: {nombre_archivo_s3}"))
        page.dialog.open = True
        page.update()

    #PANTALLA DE INICIO PARA TECNÓLOGO
    def inicio_sesion_previo():
        return View("/inicio_sesion_previo", [
        Container(  # Contenedor principal con color de fondo específico
            content=Stack(
                controls=[
                    # Imagen de semicírculo en la parte izquierda, centrado verticalmente
                    Container(
                        content=Image(src=ruta_imagen_semicirculo, fit="contain", width=200, height=400),
                        alignment=ft.alignment.center_left,  # Alineación a la izquierda y centrada verticalmente
                        padding=ft.padding.only(left=-40, bottom=-60)
                    ),
                    # Imagen del doctor en la esquina inferior derecha (mueve esta capa atrás)
                    Container(
                        content=Image(src=ruta_imagen_doctor, width=150, height=300, fit="contain"),
                        alignment=ft.alignment.bottom_right,
                        padding=ft.padding.only(right=-20, bottom=-60)
                    ),
                    # Contenido con botones y logo (mantenlo adelante para que los botones sean interactivos)
                    Column(
                        [
                            Container(
                                content=Image(src=ruta_logo, width=300, height=300),
                                padding=ft.padding.only(top=70)
                            ),
                            Text("Bienvenido a EYERIS - Ayudando en el descarte de glaucoma", size=18, weight="bold"),
                            # Botón 1
                            Container(
                                content=ElevatedButton(
                                    "Iniciar Evaluación", 
                                    on_click=lambda e: ingreso(),
                                    bgcolor="#9e9ec7",
                                    color="#ffffff",
                                    height=50,  # Tamaño más pequeño
                                    width=220  # Ajuste del ancho del botón
                                ),
                                padding=ft.padding.symmetric(vertical=10)  # Espacio entre botones
                            ),
                            # Botón 2
                            Container(
                                content=ElevatedButton(
                                    "Resultados del paciente", 
                                    on_click=lambda e: change_route(e, "/reporte_pacientes"),
                                    bgcolor="#9e9ec7",
                                    color="#ffffff",
                                    height=50,
                                    width=220
                                ),
                                padding=ft.padding.symmetric(vertical=10)
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    )
                ],
            ),
            bgcolor="#d1d2db",  # Color de fondo especificado
            expand=True
        )
    ])

    def ingreso():
        page.launch_url("http://10.100.196.153:8501")

    def reporte_pacientes():

        
        dni_input = TextField(label="Ingrese el DNI del paciente", width=300, bgcolor="#f7bf70", color="#000002", border_radius=20)
        nombres = TextField(label="Ingrese el nombre del paciente", width=300, bgcolor="#f7bf70", color="#000002", border_radius=20)
        buscar_button = ElevatedButton("Buscar paciente", on_click=lambda e: mostrar_reporte(dni_input.value), bgcolor="#c6d8e3", color="#020202")
        volver_button = ElevatedButton("Volver al inicio", on_click=lambda e: change_route(e, "/inicio_sesion_previo"), bgcolor="#c6d8e3", color="#020202")

        # Contenedor principal con el color de fondo deseado
        main_container = Container(
            content=Column(
                [
                    Text("Buscar Reporte del paciente", size=20, weight="bold"),
                    dni_input,
                    nombres,
                    Row([buscar_button, volver_button], alignment=ft.MainAxisAlignment.CENTER, spacing=10)  # Espaciado entre botones
                ],
                spacing=20,  # Espacio entre los elementos de la columna
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            ),
            bgcolor="#d1d2db",  # Color de fondo de todo el contenedor
            padding=20,  # Espacio alrededor del contenido dentro del contenedor
            expand=True
        )

        return View("/reporte_pacientes", [main_container])
    
    def mostrar_reporte(dni):
        # Generar el nombre del archivo en S3 a partir del DNI
        archivo_s3 = f"{dni}.xlsx"
    
        try:
            # Verificar si el archivo existe en S3
            s3_client.head_object(Bucket=bucket_name, Key=archivo_s3)
        
            # Generar URL pública (o firmada) para el archivo
            url_reporte = f"https://{bucket_name}.s3.us-east-2.amazonaws.com/{archivo_s3}"
            url_reporte = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': archivo_s3},
                ExpiresIn=3600  # URL válida por 1 hora
            )

            # Mostrar un diálogo notificando al usuario que el archivo está disponible
            dialog = ft.AlertDialog(
                title=ft.Text(f"El reporte para el DNI: {dni} está disponible."),
                on_dismiss=lambda e: print("Descargando el reporte...")
            )
            page.overlay.append(dialog)
            page.update()

            # Abrir el enlace en el navegador
            page.launch_url(url_reporte)

        except ClientError as e:
            # Manejar el caso en que el archivo no existe o hay un error en S3
            if e.response['Error']['Code'] == "404":
                dialog = ft.AlertDialog(
                    title=ft.Text(f"No se encontró ningún reporte para el DNI: {dni}"),
                    on_dismiss=lambda e: print("Error: Archivo no encontrado en S3.")
                )
            else:
                dialog = ft.AlertDialog(
                    title=ft.Text(f"Error al buscar el reporte: {e.response['Error']['Message']}"),
                    on_dismiss=lambda e: print("Error: Problema con S3.")
                )
            page.overlay.append(dialog)
            page.update()
        except NoCredentialsError:
            print("Error: Credenciales de AWS no configuradas correctamente.")
    


    page.views.append(inicio())
    page.update()

ft.app(target=main, port=int(os.environ.get("PORT", 8080)))