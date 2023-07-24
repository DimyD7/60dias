import re
import pymssql
import pandas as pd
import plotly.graph_objs as go
import openai 
import json
from dash import Dash, dcc, html, Input, Output, State
import dash_loading_spinners as dls
from flask import Flask

server = '60d-az-sql001.database.windows.net'
database = 'DatamartDB'
username = 'sqladmin'
password = 'ALvRu6MwLpV2f3s'
port="1433"


openai.api_key = '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'

servidor = Flask(__name__)
external_stylesheets = ['assets/styles.css']
app = Dash(server=servidor, external_stylesheets=external_stylesheets)
app.title = 'Dashboard'


### Encabezado
header=html.Div(id='header', children=[
    html.Img(id="img",src=app.get_asset_url('images/logo.png'),style={'width': 'auto', 'height': '40px'}),
    dcc.Dropdown(
    id='loggin',
    options=[
        {'label': 'Altia', 'value': 123635},
        {'label': 'PWHC AUDITORES', 'value': 124517},
        {'label': 'Admin', 'value': 124516}
    ],
    value=124516, style={'width': '33%', 'display': 'inline-block', 'verticalAlign': 'top', 'textAlign': 'center'}),
    html.Hr(style={'color':'gray'})]
    )



# Cuadro de chat
chat = html.Div(
    children=[
        html.Div(id='output',children=[],className='chat-history'),
    ]
)
'''
# Cuadro de chat
chat = dls.Hash(html.Div(
    children=[
        html.Div(id='output',children=[],className='chat-history',),
    ]
))
'''
# Prguntas frecuentes
questions=html.Div(id='questions',className='questions', 
                   children=[
    html.Label('Preguntas frecuentes:'),
    dcc.Dropdown(placeholder="Seleccionar una pregunta frecuente...",
    id='faqs',
    options=[
        {'label': 'Dime los empleados que utilizan el taxi, la cantidad de veces que lo usan, el precio que pagan y la distancia que recorren', 'value': 'Dime los empleados que utilizan el taxi, la cantidad de veces que lo usan, el precio que pagan y la distancia que recorren'},
        {'label': 'Dame algún otro ejemplo', 'value': 'Dame algún otro ejemplo'},
        {'label': 'Muestrame los empleados que más veces usan el taxi', 'value': 'Muestrame los empleados que más veces usan el taxi'},
        {'label': 'Muestrame el número de ticktes por mes del año 2022', 'value': 'Muestrame el número de ticktes por mes del año 2022'}
    ],
    value='')]
    )

chat_interaccion = html.Div([
        dcc.Input(id='input', type='text', value=''),
        html.Button(id='chat-button',n_clicks=0, children=html.Img(id="img_button",src=app.get_asset_url('images/send_button.png')))
    ], className='chat-interaction')



###Layout
app.layout = html.Div([
    header,
    chat,
    questions,
    chat_interaccion,
    html.Hr(style={'color':'blue'}),
    dcc.Tabs([
        # Tabla de datos
        dcc.Tab(label='Tabla',id="tab1" ,children=[
            html.Div([
                html.Br(),
                html.Div(id="tabla", className="table-wrapper")])]),
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
    ])
])


context = []
conversacion = []
consulta=""

@app.callback(
    [Output('output', 'children'), Output('input', 'value'),Output('faqs', 'value'), Output('eje-x', 'value'), Output('eje-y', 'value')],
    [Input('chat-button', 'n_clicks'),Input('loggin','value')],
    [State('faqs', 'value'),State('input', 'value'), State('output', 'children')]
)
def collect_messages(n_clicks, cliente,faqs_value,input_value, output_value):
    global context,conversacion  

    if n_clicks > 0 and (input_value or faqs_value):
        if faqs_value:
            input_value = faqs_value
            
        else:
            input_value = input_value
        
        prompt = input_value

        # Agrega el mensaje del usuario al contexto de la conversación
        context.append({'role': 'user', 'content': f"{prompt}"})

        # Realiza la respuesta del Chatbot
        response = get_completion_from_messages(context)

        # Agrega el mensaje del Chatbot al contexto de la conversación
        context.append({'role': 'assistant', 'content': f"{response}"})

        # Actualiza el historial de conversación
        conversacion.insert(0,html.Div(f"User: {input_value}", className='user-message'))
        conversacion.insert(0,html.Div(f"Chatbot: {response}", className='chatbot-message'))

        
        df=get_data()
        
        if len(df)==0:
            conversacion.insert(0,html.Div("No se muestran datos para la consulta planteada", className='chatbot-message')) 
        
        else:
        
            #df_json = df.to_json(orient='records')
            
            prompt = f"""
            Eres un experto consultor de datos. Quiero que me analices los siguiente datos ```{df}```\
                y me devuelvas formato JSON:
                    - titulo: basate en la pregunta realizada o en la pregunta sugerida fijate en el contenido de los dos ultimos elementos de ```{context}```
                    - conclusiones: listado, muestra en 3 y 6.
                    - resumen: breve parrafo indiando el analisis realizado y la mejor forma de visualizar los gráficos, grafico de barras, de tarta, que poner en valores y en etiquetas.
                    
            Sólo muestra el JSON, nada más."""
            
            messages = [{"role": "user", "content": prompt}]
            
            analysis = get_completion_from_messages(messages)
            
            respuesta_json = json.loads(analysis)
            
            analysis=html.Div([html.H3(respuesta_json["titulo"]) ,      
                html.Ul([html.Li(con) for con in respuesta_json["conclusiones"]]),
                html.P(respuesta_json["titulo"])
                ],className='chatbot-message')
        
            conversacion.insert(0,analysis)  

        return conversacion, '', '','',''
    else:
        # Restablece el contexto y el historial de conversación cuando se carga la página
        context = [{'role': 'system', 'content': f"""Eres un experto consultor de datos.
                    Te van a hacer preguntas sobre los datos almacenados en la vista Tickets_Analytics que esta almacenada en una BBDD de sql server. 
                    Sólo puedes ofrecer información de esta vista, de ninguna otra. Para ello vas a generar consultas SQL Server para poder obtener los datos.
                        
        Tickets_Analytics:
        - idTicket: identificador del ticket
        - cantidad: dependiendo de la tipología puede indicar una u otra cosa 
            - número de productos
        - precio: precio de los productos. Debes tener en cuenta la cantidad, el precio del producto es Precio/Cantidad
        - personas: núero de personas
        - categoría: Categoría del producto
        - subcategoría: Subcatecoría
        - marca
        - tipo
        - Tipología: Clasificación del ticket
            - Taxis: Muestra los tickets que son de tipo taxi
            - Restaurantes: Muestra los tickets que son de tipo restaurante
        - Empleado: Nombre del empleado asociado al ticket
        - idCliente: Identificador del cliente, tipo numércio. Cada cliente sólo puede ver sus tickets, por ello debes tenerlo en cuenta a la hora de mostrar las consultas. Valor es ```{cliente}```.
        No debes permitir que se puedan consultar los tiques para otro identificador que no coincida con ```{cliente}```
        
        Debes devolver al usuario siempre una respuesta amable indicando que tiene a disposición una tabla con los datos solicitados y que puede visualizarlos
        en un gráfico y tambien debes proporcionar la consulta sql server que generes, esta debe empezar por SELECT y terminar por punto y coma.
        
        Quiero que saludes cordialmente y preguntes qué información acerca de los tickets desea conocer. 
        A continuación te muestro un par de ejemplos de cuestiones que te pueden hacer:
             - Ejemplo 1: 
                 - Pregunta: Productos más consumidos
                 - Respuesta: Aquí tienes los 10 productos que más se han consumido
                 - Consulta: SELECT TOP 10 subcategoria, SUM(cantidad) AS total_consumido FROM Tickets_Analytics where idCliente = ```{cliente}``` GROUP BY marcas ORDER BY total_consumido DESC ;
             - Ejemplo 2:
                 - Pregunta: Dime el restaurante donde más barato está el agua
                 - Respuesta: Aquí tienes el ticket donde el agua está más barata
                 - Consulta: SELECT TOP 1 idTicket, precio FROM Tickets_Analytics WHERE subcategoria = 'agua' ORDER BY precio ASC where idCliente = ```{cliente}```;
             
        Si pregunta cualquier otra cosa, responde amablemente que sólo ofreces información acerca de los tickes y muestrale alguno de los ejemplos anteriores.
        
        Da una bienvenida formal y amable. Solicita que tipos de datos necesita saber e indica que tiene displible el listado de preguntas ```{faqs_value}```.
        """}]

        response = get_completion_from_messages(context)

        # Actualiza el historial de conversación
        conversacion.insert(0,html.Div(f"Chatbot: {response}", className='chatbot-message'))

        return conversacion, '', '', '', ''


def get_completion_from_messages(messages, model="gpt-3.5-turbo", temperature=0):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, # this is the degree of randomness of the model's output
    )
#     print(str(response.choices[0].message))
    return response.choices[0].message["content"]


### Parte de la web donde se meustra la tabla de la consulta realizada

@app.callback(
    Output('tabla', 'children'),
    [Input('output', 'children')]
)

def update_data(output_children):
   
    
    df=get_data()
    
    if len(df)>0:
    
        tab1=html.Div([
            html.Table([
                html.Thead(
                    html.Tr([html.Th(col) for col in df.columns])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(df.iloc[i][col]) for col in df.columns
                    ]) for i in range(len(df))
                ])
            ])
        ])
        return tab1
    
    else:
        return ''

def get_data():
    
    try:
        conn = pymssql.connect(server=server, port=port, user=username, password=password, database=database)
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

   
# Iniciar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)
