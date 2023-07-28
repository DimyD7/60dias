# - *- coding: utf- 8 - *-

from flask import Flask
import re
import pymssql
import pandas as pd
import plotly.graph_objs as go
import openai 
import json
from dash import Dash, dcc, html, Input, Output, State, dash_table, callback_context, ALL
import dash_loading_spinners as dls
import requests
import os
import base64


# Configurar el registro

host = '60d-az-sql001.database.windows.net'
database = 'DatamartDB'
username_db = 'sqladmin'
password_db = 'ALvRu6MwLpV2f3s'
port="1433"

context = []
conversacion = []
consulta=""

openai.api_key = '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'

servidor = Flask(__name__)
external_stylesheets = ['assets/styles.css']
app = Dash(server=servidor, external_stylesheets=external_stylesheets)
app.title = 'Dashboard'

########################################################################################### LOGIN #####################################################################################################
login_layout = html.Div(
    className='login-container',
    children=[
        html.Div(
            className='logo-container',
            children=[
                html.Img(id="img", src=app.get_asset_url('images/logo.png'), className='logo')
            ]
        ),
        html.Div(
            className='credentials-container',
            children=[
                html.Img(id="img", src=app.get_asset_url('images/minilogo60.jpg'), className='minilogo'),
                html.Div(
                    className='input-container',
                    children=[
                        html.H1('Consulta', className='login-title'),
                        html.H1('todos tus tickets', className='login-subtitle1'),
                    ],
                ),
                html.Div(
                    className='input-container',
                    children=[
                        html.Label('Nombre de usuario:', className='login-label'),
                        dcc.Input(id='username-input', type='text', className='login-input'),
                    ],
                ),
                html.Div(
                    className='input-container',
                    children=[
                        html.Label('Contraseña:', className='login-label'),
                        dcc.Input(id='password-input', type='password', className='login-input'),
                    ],
                ),
                html.Div(
                    className='input-container',
                    children=[
                        html.Button('Iniciar sesión', id='login-button', n_clicks=0, className='login-button')
                    ],
                ),
                html.Div(id='login-output', className='login-output')
            ],
        ),
    ],
)



# Callback para manejar el inicio de sesión
@app.callback(
    Output('login-output', 'children'),
    [Input('login-button', 'n_clicks')],
    [State('username-input', 'value'), State('password-input', 'value')]
)
def login(n_clicks, username, password):

    if n_clicks > 0:
        conn = pymssql.connect(server=host, port=port, user=username_db, password=password_db, database=database)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM Analytics_Usuarios WHERE usuario='{username}' AND password='{password}'")
        row = cursor.fetchone()
        if row:
            # Redirigir a la página del dashboard si las credenciales son correctas
            return dcc.Location(pathname=f'/dashboard/{username}', id='login-success')
        else:
            return html.Div('Credenciales inválidas.')
        


########################################################################################################################################################################################################


########################################################################################### MAIN #######################################################################################################

header = html.Div(
    children=[
        html.Div(
            className='encabezado',
            children=[html.Div(
                className='encabezado-logo',children=[
                    html.Img(
                        id="img",
                        src=app.get_asset_url('images/logo.png'),
                        className='encabezado-img',
                    )]),
                    html.Div(
                        className='desconectar',
                        children=[
                            html.Button(
                                children=[
                                    html.Div(
                                        children=[
                                            html.Img(id="img", src=app.get_asset_url('images/opcion-de-cerrar-sesion.png'),title='Desconectar'),  # Icono de desconectar utilizando dash-fontawesome
                                            html.Span('Desconectar')  # Texto del botón
                                        ],
                                        className='desconectar-button'
                                    )
                                ],
                                id='desconectar',
                                n_clicks=0
                            )
                        ]
                    ),
                html.Div(
                    className='usuario',
                    children=[
                        html.Div(
                            children=[
                                html.Img(id="img", src=app.get_asset_url('images/usuario-de-perfil.png')),  # Icono de usuario utilizando dash-fontawesome
                                html.Span(id='username-display', children=[])  # Texto del botón (se actualiza con el nombre de usuario)
                            ],
                        className='usuario-button')
                    ]
                )
            ]
        ),
        html.Hr()
    ]
)



# Cuadro de chat
chat =dls.Hash(html.Div(
    className="franja-chat",
    children=[
        html.Div(id='output',children=[],className='chat-history'),
    ]
))


chat_interaccion = html.Div([
        html.Button(className='como-preguntar',children=[html.Img(id="img", src=app.get_asset_url('images/ayudar.png'),title='Como preguntar')],id='como-preguntar',n_clicks=0),
        dcc.Input(id='input',className="barra-input", type='text', value='',placeholder="Escriba aquí su consulta..."),
        html.Button(id='chat-button',n_clicks=0, children=[html.Img(id="img_button",src=app.get_asset_url('images/send_button0.png'))],className='recuadro-boton0',disabled=True)
    ], className='chat-interaction')


tipos_tickets= html.Div([
        html.Button(className='tickets-tipos',children=[html.Img(id="img", src=app.get_asset_url('images/factura.png'),title='Tipos de tickets')],id='tipos-tickets',n_clicks=0),
        dcc.Checklist(
                    id='tipologia',
                    options=[
                        {'label': 'Taxis', 'value': 'Taxis'},
                        {'label': 'Restaurantes', 'value': 'Restaurantes'},
                        {'label': 'Gasolineras', 'value': 'Gasolineras'},
                    ],
                    value=[],
                    inline=True,
                    labelStyle={"margin-right": "1rem"},
                    className='typologies-values'
                )
        ], className='typologies-tickets')


zona_chat =  html.Div(className='chatbox',children = [
        chat,
        chat_interaccion,
        tipos_tickets
        
    ]
    )



tabs=html.Div(id='tabs',className='tabs', 
                   children=[html.Hr(style={'color':'blue'}),
                             dcc.Tabs([
                                 # Tabla de datos
                                 dcc.Tab(label='Tabla',id="tab1", children=[
                                     html.Div([
                                         html.Br(),
                                         html.Div(id="tabla", className="table-wrapper"),
                                         html.Div(id='image-container',className="image-ticket")])]),
                                 # Selector de gráfico
                                 dcc.Tab(label='Gráfico',id="tab2", children=[
                                     html.Div([
                                         html.Br(),
                                         html.Label('Selecciona una tipo de gráfico:'),
                                         dcc.Dropdown(
                                         id='tipo-grafico',
                                         options=[
                                             {'label': 'Gráfico de tarta', 'value': 'sectores'},
                                             {'label': 'Gráfico de barras', 'value': 'barras'}
                                         ],
                                         value='barras'
                                     )], style={'width': '33%', 'display': 'inline-block', 'verticalAlign': 'top', 'textAlign': 'center'}),
                                 # Selectores de ejes
                                 html.Div([
                                     html.Br(),
                                     html.Label('Etiquetas:'),
                                     dcc.Dropdown(id='eje-x',placeholder='Seleccionar columna...')], style={'width': '33%', 'display': 'inline-block', 'verticalAlign': 'top', 'textAlign': 'center'}),
                                 html.Div([
                                     html.Br(),
                                     html.Label('Valores:'),
                                     dcc.Dropdown(id='eje-y',placeholder='Seleccionar columna...')], style={'width': '33%', 'display': 'inline-block', 'verticalAlign': 'top', 'textAlign': 'center'}),
                                 html.Br(),
                                 dcc.Graph(id='grafico')])
                             ])])

###Layout
layout_dashboard = html.Div([
    header,
    html.H1("Consulta tus tickets"),
    zona_chat,
    tabs
])




@app.callback(Output('username-display', 'children'),
              [Input('url', 'pathname')])

def display_username(pathname):
    username = pathname.split('/')[-1]  # Obtener el último elemento de la URL como el nombre de usuario
    if username:
        return f'{username.capitalize()}'
    else:
        return ''

@app.callback(
    [Output('output', 'children'), Output('eje-x', 'value'), Output('eje-y', 'value'),Output('como-preguntar', 'n_clicks')],
    [Input('chat-button', 'n_clicks'),Input('como-preguntar', 'n_clicks')],
    [State('tipologia', 'value'),State('url', 'pathname'),State('input', 'value'), State('output', 'children')])

def collect_messages(n_clicks,como_preguntar,tipologia, cliente,input_value, output_value):
    global context,conversacion 
        
    cliente = cliente.split('/')[-1]

    query = f""" SELECT idGrupo
                from Analytics_Usuarios au 
                where usuario = '{cliente}'
            """
    
    conn = pymssql.connect(server=host, port=port, user=username_db, password=password_db, database=database)
    cursor = conn.cursor()

    cursor.execute(query)
    grupo = cursor.fetchone()[0]
    
 
    cliente = grupo
    
    if como_preguntar > 0:
        
        como_pregutnar = []
        como_pregutnar.append(html.Span("Puedes preguntar escribiendo en el cuadro de texto o seleccionando una pregunta frecuente"))
        como_pregutnar.append(html.Br())
        
        preguntas=["Múestrame todos los tickets","Tickets de mayor precio"]
        
    
        for i in range(len(preguntas)):
            como_pregutnar.append(html.Button( f'{preguntas[i]}',id={'type': 'dynamic-button', 'index': i+1,'value': f'{preguntas[i]}'}))
            #como_pregutnar.append(html.Button(f"{preguntas[i]}", id=f"boton-{i+1}", n_clicks=0))
        
        mensaje_icono_chat = html.Div(
        children=[
            html.Img(id="img", src=app.get_asset_url('images/bot.png'),className='mensaje-icono-chatbot'),
            html.Div(como_pregutnar, className='chatbot-message')
        ])
        
        conversacion.insert(0,mensaje_icono_chat) 
        
       
        return conversacion, '', '', 0
     
    elif n_clicks > 0 and input_value:
        
        if tipologia:               
            prompt = input_value  + " y que la tipgolia sea " + ' y '.join(tipologia) 
        else: 
            prompt = input_value

        # Agrega el mensaje del usuario al contexto de la conversación
        context.append({'role': 'user', 'content': f"{prompt}"})

        # Realiza la respuesta del Chatbot
        response = get_completion_from_messages(context)

        # Agrega el mensaje del Chatbot al contexto de la conversación
        context.append({'role': 'assistant', 'content': f"{response}"})

        
        mensaje_icono_user = html.Div(
            children=[
                html.Img(id="img", src=app.get_asset_url('images/usuario.png'),className='mensaje-icono-user'),
                html.Div(input_value, className='user-message')
                
                ]
        )

        conversacion.insert(0,mensaje_icono_user)
        
        # mensaje_icono_chat = html.Div(
        #     children=[
        #         html.Img(id="img", src=app.get_asset_url('images/bot.png'),className='mensaje-icono-chatbot') ,
        #         html.Div(f"{response}", className='chatbot-message')]
        # )
        
        # conversacion.insert(0,mensaje_icono_chat)
        
        
        df=get_data()
        
        
        if len(df)==0:
            
            #conversacion.insert(0,html.Img(id="img", src=app.get_asset_url('images/BOT.png'),className='mensaje-icono-chatbot'))
            #conversacion.insert(0,html.Div("No se muestran datos para la consulta planteada", className='chatbot-message')) 
        
            mensaje_icono_chat = html.Div(
            children=[
                html.Img(id="img", src=app.get_asset_url('images/bot.png'),className='mensaje-icono-chatbot') ,
                html.Div("No se muestran datos para la consulta planteada", className='chatbot-message')]
            )
            
            conversacion.insert(0,mensaje_icono_chat) 
        
        else:
        
            #df_json = df.to_json(orient='records')
            
            prompt = f"""
            Eres un experto consultor de datos. Quiero que me analices los siguiente datos ```{df}```\
                y me devuelvas formato JSON:
                    - titulo: basate en la pregunta realizada o en la pregunta sugerida fijate en el contenido de los dos ultimos elementos de ```{context}```
                    - conclusiones: listado, muestra en 3 y 6.
                    - resumen: breve parrafo indiando el analisis realizado y la mejor forma de visualizar los gráficos, grafico de barras, de tarta, que poner en valores y en etiquetas.
                    - preguntas: un listado de preguntas que se pueden hacer como sugerencia para tener más inforamción de los datos. Entre 1 y 5
                    
            Sólo muestra el JSON, nada más."""
            
            messages = [{"role": "user", "content": prompt}]
            
            analysis_messages = get_completion_from_messages(messages)
            
            respuesta_json = json.loads(analysis_messages)
            
            preguntas = respuesta_json["preguntas"]
            
            analysis=[]
            
            analysis.append(html.H3(respuesta_json["titulo"]))
            analysis.append(html.Ul([html.Li(con) for con in respuesta_json["conclusiones"]]))
            analysis.append(html.P(respuesta_json["resumen"]))
            analysis.append(html.Br())
            
            
            for i in range(len(preguntas)):
                analysis.append(html.Button( f'{preguntas[i]}',id={'type': 'dynamic-button', 'index': i+1,'value': f'{preguntas[i]}'}))


            
            mensaje_icono_chat = html.Div(
            children=[
                html.Img(id="img", src=app.get_asset_url('images/bot.png'),className='mensaje-icono-chatbot') ,
                html.Div(analysis,className='chatbot-message')]
            )
            
           
            conversacion.insert(0,mensaje_icono_chat)  

        return conversacion, '', '', 0
    else:
        # Restablece el contexto y el historial de conversación cuando se carga la página
        context = [{'role': 'system', 'content': f"""Eres un experto consultor de datos.
                    Te van a hacer preguntas sobre los datos almacenados en la vista Tickets_Analytics que esta almacenada en una BBDD de sql server. 
                    Sólo puedes ofrecer información de esta vista, de ninguna otra. Para ello vas a generar consultas SQL Server para poder obtener los datos.
                    Esta consulta sql server debe empezar por SELECT y terminar por punto y coma.
        A continuación te doy información de las columnas que tiene dicha vista.                
        Tickets_Analytics:
        - idTicket: identificador del ticket
        - cantidad: dependiendo de la tipología puede indicar una u otra cosa 
            - número de productos
        - precio: precio de los productos. Debes tener en cuenta la cantidad, el precio del producto es Precio/Cantidad
        - personas: núero de personas
        - categoria: Categoría del producto
        - subcategoria: Subcatecoría
        - marca
        - tipo
        - Tipologia: Clasificación del ticket
            - Taxis: Muestra los tickets que son de tipo taxi
            - Restaurantes: Muestra los tickets que son de tipo restaurante
        - Empleado: Nombre del empleado asociado al ticket
        - url: url asociada de la imagen de cada ticket, cada vez que te pregunten por los tickets incluye este campo en la consulta
        - idCliente: Identificador del cliente, tipo numéricio
        - Cliente: Nombre del cliente
        - idGrupo: Identificador del grupo, tipo numércio. Cada grupo sólo puede ver sus tickets, por ello debes tenerlo en cuenta a la hora de mostrar las consultas. Valor es ```{cliente}```.
        No debes permitir que se puedan consultar los tiques para otro identificador que no coincida con ```{cliente}```
        
        A continuación te muestro un par de ejemplos de preguntas que te pueden hacer, caul debe ser la respuesta y cual la consulta generada:
             - Ejemplo 1: 
                 - Pregunta: Productos más consumidos
                 - Respuesta: Aquí tienes los 10 productos que más se han consumido
                 - Consulta: SELECT TOP 10 subcategoria, SUM(cantidad) AS total_consumido FROM Tickets_Analytics where idGrupo = ```{cliente}``` GROUP BY marcas ORDER BY total_consumido DESC ;
             - Ejemplo 2:
                 - Pregunta: Dime el restaurante donde más barato está el agua
                 - Respuesta: Aquí tienes el ticket donde el agua está más barata
                 - Consulta: SELECT TOP 1 idTicket, precio FROM Tickets_Analytics WHERE subcategoria = 'agua' ORDER BY precio ASC where idGrupo = ```{cliente}```;
             - Ejemplo 3:
                 - Pregunta: Tickets mayor precio
                 - Respuesta: Aquí tienes el top 10 de los tickets de mayor precio
                 - Consulta: SELECT TOP 10 idTicket, precio, url FROM Tickets_Analytics WHERE idGrupo = ```{cliente}``` ORDER BY precio DESC

        
        La primera vez quiero que saludes cordialmente y preguntes qué información acerca de los tickets desea conocer. 
        
        Una vez que se te pregunte algo debes devolver al usuario siempre una respuesta amable indicando que a continuaicón tiene una análisis de los datos y que tambien dispone
        de una tabla con los datos solicitados y que puede visualizarlos en un gráfico.
                    
        Si pregunta cualquier otra cosa, responde amablemente que sólo ofreces información acerca de los tickes y muestrale alguno de los ejemplos anteriores.
        
        Si te preguntan en algún momento por las columnas devuelve también la consulta sql server que extrae los nombres de las columnas de una vista.
        """}]

        response = get_completion_from_messages(context)
        
        mensaje_icono = html.Div(
            children=[
                html.Img(id="img", src=app.get_asset_url('images/bot.png'),className='mensaje-icono-chatbot'),
                html.Div(f"{response}", className='chatbot-message')]
        )
        
        conversacion.insert(0,mensaje_icono)
        

        return conversacion, '', '', 0


def get_completion_from_messages(messages, model="gpt-3.5-turbo", temperature=0):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, # this is the degree of randomness of the model's output
    )
#     print(str(response.choices[0].message))
    return response.choices[0].message["content"]


@app.callback(
    [ Output('chat-button', 'children'),Output('chat-button', 'className'),Output('chat-button', 'disabled')],
    [Input('input', 'value')])

def button_send(input_value):
    if input_value:      
        return html.Img(id="img_button",src=app.get_asset_url('images/send_button1.png')),'recuadro-boton1',not input_value
    else:
        return html.Img(id="img_button",src=app.get_asset_url('images/send_button0.png')),'recuadro-boton0','disabled'


@app.callback(
    Output('input', 'value',allow_duplicate=True),
    [Input('eje-x', 'value')],
    prevent_initial_call=True
)
def update_user_input(eje_x):
    return eje_x

@app.callback(
    Output('input', 'value'),
    [Input({'type': 'dynamic-button', 'index': ALL,'value': ALL}, 'n_clicks')],
    [State({"type": "dynamic-button", "index": ALL,'value': ALL}, "value")]

)
def update_input_box(button_clicks,valores):
    ctx = callback_context
    if button_clicks:

        #btn_number=json.loads(ctx.triggered[0]['prop_id'].split('.')[0])["index"]
        btn_value=json.loads(ctx.triggered[0]['prop_id'].split('.')[0])["value"]
        return btn_value
    return ""


@app.callback(
    [Output('tipologia', 'className'),Output('tipos-tickets','className')],
    [Input('tipos-tickets', 'n_clicks')],
)

def tipos_tickets(n_clicks):
    if n_clicks % 2 == 0 :  
        return 'typologies-values', 'tickets-tipos'
    else:        
       return 'typologies-values2', 'tickets-tipos2'




### Parte de la web donde se meustra la tabla de la consulta realizada

@app.callback(
    Output('tabla', 'children'),
    [Input('output', 'children')]
)

def update_data(output_children):
   
    df=get_data()

    
    if len(df)>0:

        # columns=[]
        # for i in df.columns:
        #     if i == "url":
        #         columns.append({"name": i, "id": i,"deletable": True,  "hidden": True})
        #     else:
        #         columns.append({"name": i, "id": i,"deletable": True, "hidden": True})
        
        tab1 = dash_table.DataTable(id='table',
                           
                data=df.to_dict("records"),               
                columns=[{"name": i, "id": i,"deletable": True} for i in df.columns],
                column_selectable="single",
                fixed_columns={'headers': True},
                hidden_columns=["url"],
                #toggleable=False,
                #export_format='csv',
                export_format='csv',
                #download_button=True,
                #download_format="csv",
                #download_button_text="Descargar",
                #download_icon="download",
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                filter_options={"placeholder_text": "Filtrar..."},
                page_size=10,
                #tooltip_data=[{'idTicket': {'value': f"!{df['idTicket'][i]}({df['URL'][i]})", 'type': 'markdown'}} for i in range(len(df))],
                # Overflow into ellipsis 
                style_cell={
                    'overflow': 'visible',
                    'textOverflow': 'clip',
                    'maxWidth': '20em',
                },
                tooltip_delay=0,
                tooltip_duration=None,
                style_data={
                    'color': 'black',
                    'backgroundColor': 'white'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(220, 220, 220)'
                        }
                ]+[{'if': {'column_id': 'idTicket'},
                                        'cursor': 'pointer',
                                    }],
                style_header={
                    'backgroundColor': 'rgb(210, 210, 210)',
                    'color': 'black',
                    'fontWeight': 'bold'
                })    
    
        return tab1

    else:
        return ''

def get_data():

    try:
        conn = pymssql.connect(server=host, port=port, user=username_db, password=password_db, database=database)
        cursor = conn.cursor()
        # Definir el patrón de la expresión regular
        patron = r"SELECT.*?;"
        # Buscar la consulta SQL utilizando la expresión regular
        resultado=re.search(patron, context[-1]["content"], re.DOTALL)

        #resultado=re.search(patron,conversacion[0],re.DOTALL)
    
        if resultado:
            query = resultado.group(0)
        else:
            query = None
                 
        try:
            cursor.execute(query)
    
        except:    
            query="SELECT TOP 10 * FROM Tickets_Analytics where idCliente = 'nothting';"
            cursor.execute(query)
    
         
           
        data=cursor.fetchall()
        col_names=[desc[0] for desc in cursor.description]
        
        df = pd.DataFrame (data, columns = col_names)
        
        return df
    except:
        df = pd.DataFrame()
        return df



###imagen ticket
@app.callback(
    Output('image-container', 'children'),
    [Input('table', 'active_cell')],
    [State('table', 'data')]
)
def display_image(active_cell, data):
    if active_cell:
        ticket = data[active_cell['row']]['idTicket']
        image_url = data[active_cell['row']]['url']
        if active_cell['column_id'] == 'idTicket':
            
            response = requests.get(image_url)
        
            if response.status_code == 200:
                file_name = os.getcwd()+'/assets/ticket.pdf'
                with open(file_name, "wb") as file:
                    file.write(response.content)
            
            with open(os.getcwd()+'/assets/ticket.pdf', 'rb') as pdf:
                pdf_data = base64.b64encode(pdf.read()).decode('utf-8')
            
            return html.Div([html.H3(ticket),html.ObjectEl(
                data='data:application/pdf;base64,'+ pdf_data,
                type="application/pdf",
                style={"width": "400px", "height": "600px"}
            )])



### Parte de la web en la que se muestra el gráfico con sus respectivos ejes

@app.callback([Output('eje-x', 'options'), Output('eje-y', 'options')],
              [Input('tipo-grafico', 'value'),Input('output', 'children')])

def actualizar_selectores(tipo_grafico,output_children):
    df=get_data()
    
    columnas = [{'label': col, 'value': col} for col in df.columns]
    return columnas, columnas
        
# Callback para generar el gráfico en función de los selectores
@app.callback(Output('grafico', 'figure'),
              [Input('tipo-grafico', 'value'), Input('eje-x', 'value'), Input('eje-y', 'value'),Input('output', 'children')])
def generar_grafico(tipo_grafico, eje_x, eje_y,output_children):
    df=get_data()
    
    if len(df)==0:
        return {}
    else:
    
        if tipo_grafico and eje_x and eje_y:
            if tipo_grafico == 'sectores':
                labels = df[eje_x].values.tolist()
                values = df[eje_y].values.tolist()
        
                data=[go.Pie(labels=labels, values=values)]
                
            elif tipo_grafico == 'barras':
                data = [go.Bar(x=df[eje_x], y=df[eje_y])]
                
            layout = go.Layout(title=tipo_grafico, xaxis_title=eje_x, yaxis_title=eje_y)
            return {'data': data, 'layout': layout}
    
        else:
            return {}

   

# Diseño de la aplicación Dash con múltiples páginas
app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=True),
        html.Div(id='page-content')
    ]
)



# Callback para el boton de desconectar
@app.callback([Output('url', 'pathname'),Output('desconectar', 'n_clicks')]
              ,Input('desconectar', 'n_clicks'),
              State('url', 'pathname'))
def redirect_to_login(n_clicks,url):
    global conversacion,context
    if n_clicks > 0:
        conversacion = []
        context = []
        return '/',0
    else:
        return url,0
    

# Callback para manejar la navegación entre páginas
@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    username = pathname.split('/')[-1]
    
    if pathname == f'/dashboard/{username}':
        return layout_dashboard
    else:
        return login_layout



########################################################################################################################################################################################################
# Iniciar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_hot_reload=False)
