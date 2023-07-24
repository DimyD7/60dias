import requests   
from dash import Dash, dcc, html, Input, Output, State, dash_table, callback_context, ALL, MATCH

app = Dash(__name__)

app.layout = html.Div([
    dcc.Input(id='pdf-url', type='text', placeholder='Ingresa la URL del PDF'),
    html.Button('Mostrar PDF', id='submit-button', n_clicks=0),
    html.Div(id='pdf-frame'),
    '''
    html.Iframe(src='assets/ticket.pdf',style={"width": "400px", "height": "600px"}),
    html.ObjectEl(
            # To my recollection you need to put your static files in the 'assets' folder
            data="assets/ticket.pdf",
            type="application/pdf",
            style={"width": "400px", "height": "600px"}
        )
    '''
    
])

@app.callback(
    Output('pdf-frame', 'children'),
    [Input('submit-button', 'n_clicks'),Input('pdf-url', 'value')])

def update_pdf_frame(n_clicks,pdf_url):
    
    
    if n_clicks > 0:
       
        response = requests.get(pdf_url)
        
        if response.status_code == 200:
            file_name = 'C:/Users/david.lozano/Desktop/Altia/Otros_proyectos/60dias/app/chatbot_last/assets/ticket2.pdf'
            with open(file_name, "wb") as file:
                file.write(response.content)
            
        return  html.Iframe(src='assets/ticket2.pdf',style={"width": "400px", "height": "600px"})
        #return html.Button('click')
    return ''




if __name__ == '__main__':
    app.run_server(debug=True)