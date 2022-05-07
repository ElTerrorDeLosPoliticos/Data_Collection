from flask import Flask, request, render_template
import time
import os

from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import asyncio
import httpx

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/info_proveedores/<ruc>')
async def info_proveedores(ruc):

    start_time = time.time()
    item = {}
    def normalize_datos_proveedor(req):
        datos_sunat = req["datosSunat"]
        conformacion = req["conformacion"]
        antecedentes = req["antecedentes"]
        try:
            [datos_sunat.pop(key) for key in ["ruc", "razon","resultadoT01","respuesta", "personeria", "process"]]
        except:
            pass
        try:
            [conformacion.pop(key) for key in ["resultadoT01", "process"]]
        except:
            pass
        try:
            [conformacion["proveedor"].pop(key) for key in ["personeria", "esEjecutor","codigoRegistroEjec","idDocIdent", "nroDocIdent","codigoDoc", "nombreDoc"]]
        except:
            pass
        try:
            [conformacion["socios"][n].pop(key) for n in range(len(conformacion["socios"])) for key in ["idSocio","codigoRegistro", "codigoDocIde", "numeroAcciones"]]
        except:
            pass
        try:
            [conformacion["representantes"][n].pop(key) for n in range(len(conformacion["representantes"])) for key in ["idRepresentante","codigoRegistro","codigoDocIde", "idCargo","descCargo","numeroRuc","fechaIngreso"]]
        except:
            pass
        try:
            [conformacion["organosAdm"][n].pop(key) for n in range(len(conformacion["organosAdm"])) for key in ["idOrgano","codigoRegistro","codigoDocIde","idTipoOrgano","idCargo"]]
        except:
            pass
        try:
            [conformacion.pop(key) for key in ["listaDniSocios", "listaDniRepresentantes","listaDniOrganos","fechaConsulta"]]
        except:
            pass
        try:
            [antecedentes.pop(key) for key in ["resultadoT01", "process","fechaConsultaSancTCE", "fechaConsultaInhabAD","fechaConsultaInhabMJ"]]
        except:
            pass
        conformacion["proveedor"].update(datos_sunat)
        conformacion.update(antecedentes)
        item = conformacion
        return item

    def normalize_experiencia_rnp(req):
        item = {}
        experiencia = [] 
        req = req["listaObras"]
        try:
            [req[0].pop(key) for key in ["pathName","tipConsultoria","codObra", "especialidad","expediente","esConsorcio","miembrosConsorcio","penalidad","arbitraje","num","tipoMonSimContrato"]]
        except:
            pass
        experiencia.extend(req)

        item["experiencia_rnp"]=experiencia
        return item

    def normalize_experiencia_seace(req):
        item = {}
        experiencia = []
        req = req["contratacionesT01"]
        try:
            [req[n].pop(key) for key in ["idMonMontoOrigen","esConsorcio"] for n in range(len(req))]
        except:
            pass
        experiencia.extend(req)

        item["experiencia_seace"]=experiencia
        return item

    async with httpx.AsyncClient() as client:
        datos_proveedores, experiencia_rnp, experiencia_seace = await asyncio.gather(
            client.get(f'https://eap.osce.gob.pe/ficha-proveedor-cns/1.0/ficha/{ruc}', timeout=None),
            client.get(f'https://eap.osce.gob.pe/expprov-bus/1.0/experiencia/{ruc}/?q=&pageSize=1999999999&pageNumber=1&t=1&vista=2', timeout=None),
            client.get(f'https://eap.osce.gob.pe/perfilprov-bus/1.0/ficha/{ruc}/contrataciones?pageNumber=1&searchText=&pageSize=1999999999', timeout=None),
        )
    datos_proveedores = datos_proveedores.json()
    experiencia_rnp = experiencia_rnp.json()
    experiencia_seace = experiencia_seace.json()

    all_next_pages_rnp = [f"https://eap.osce.gob.pe/expprov-bus/1.0/experiencia/{ruc}/?q=&pageSize=1999999999&pageNumber={i}&t=1&vista=2" for i in range(1, (experiencia_rnp)["searchInfo"]["pageTotal"])]
    all_next_pages_seace = [f"https://eap.osce.gob.pe/perfilprov-bus/1.0/ficha/{ruc}/contrataciones?pageNumber={i}&searchText=&pageSize=1999999999" for i in range(1, (experiencia_seace)["searchInfo"]["pageTotal"])]
   

    tmp_seace = []
    tmp_rnp = []

    if experiencia_seace["searchInfo"]["pageTotal"]!=1 and experiencia_rnp["searchInfo"]["pageTotal"]!=1:
        async with httpx.AsyncClient() as client:
            datos_rnp = await asyncio.gather(*[client.get(url, timeout=None) for url in all_next_pages_rnp] )
            datos_seace = await asyncio.gather(*[client.get(url, timeout=None) for url in all_next_pages_seace] )
            for i in datos_rnp:
                i = i.json()
                tmp_rnp.extend((normalize_experiencia_rnp(i))["experiencia_rnp"])
            for i in datos_seace:
                i = i.json()
                tmp_seace.extend((normalize_experiencia_seace(i))["experiencia_seace"])
    elif experiencia_seace["searchInfo"]["pageTotal"]!=1:
        async with httpx.AsyncClient() as client:
            datos_seace = await asyncio.gather(*[client.get(url, timeout=None) for url in all_next_pages_seace] )
            for i in datos_seace:
                tmp_seace.extend((normalize_experiencia_seace(i))["experiencia_seace"])

    elif experiencia_rnp["searchInfo"]["pageTotal"]!=1:
        async with httpx.AsyncClient() as client:
            datos_rnp = await asyncio.gather(*[client.get(url, timeout=None) for url in all_next_pages_rnp] )
            for i in datos_rnp:
                tmp_rnp.extend((normalize_experiencia_rnp(i))["experiencia_rnp"])

    else:
        pass

    datos_proveedores = normalize_datos_proveedor(datos_proveedores)
    experiencia_rnp = normalize_experiencia_rnp(experiencia_rnp)
    experiencia_seace = normalize_experiencia_seace(experiencia_seace)

    experiencia_seace["experiencia_seace"].extend(tmp_seace)
    experiencia_rnp["experiencia_rnp"].extend(tmp_rnp)
    

    item.update(datos_proveedores)
    item.update(experiencia_rnp)
    item.update(experiencia_seace)
    end_time = time.time()
    print(f"Tiempo de ejecucion: {end_time - start_time}")
    return item


@app.route('/consulta_rop/<dni>')
def consulta_rop(dni):
    url = f'https://aplicaciones007.jne.gob.pe/srop_publico/Consulta/Afiliado'
    def initial_request():
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.headless = True
        options.add_argument("--window-size=3840,2160")
        options.add_argument("--disable-extensions")
        options.add_argument("--proxy-server='direct://'")
        options.add_argument("--proxy-bypass-list=*")
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--allow-insecure-localhost')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--log-level=3")
        options.add_argument("--proxy-server=direct://")
        options.add_argument("--proxy-bypass-list=(")
        
        driver = uc.Chrome(chrome_options=options)        
        print(dni)
        driver.get(url)

        WebDriverWait(driver, 10)\
            .until(EC.element_to_be_clickable((By.XPATH,
                                            '/html/body/div[1]/div[1]/form/div/input')))\
            .send_keys(dni)
        WebDriverWait(driver, 10)\
            .until(EC.element_to_be_clickable((By.XPATH,
                                            '/html/body/div[1]/div[1]/form/button')))\
            .click()
        nombre = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div[1]/div[2]/div/table/tbody/tr[1]/td/div/p')))
        nombre = nombre.text.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")    
        partidos = [i.text.replace("\n"," ").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u") for i in driver.find_elements_by_xpath('(//span[@title])')]
        del partidos[-1]
        del partidos[-1]
        del partidos[-1]
        del partidos[-1]
        militancia = [i.text.replace("\n"," ").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u") for i in driver.find_elements_by_xpath('//table[@id="Hist_Ciudadano"]')]
        
        HistorialPartidario = {}
        for i in partidos:
            num =partidos.index(i)
            HistorialPartidario[i]=militancia[num]

            
        item = {
            'Nombre_Completo': nombre,
            'DNI': dni,
            'HistorialPartidario': HistorialPartidario,
            'Fecha_Consultada': time.strftime("%Y%m%d")
        }
       
        if item["Nombre_Completo"] == "":
            item["Nombre_Completo"] = None
        elif item['DNI'] == "":
            item['DNI'] = None
        elif item['HistorialPartidario'] == {}:
            item['HistorialPartidario'] = None

        driver.close()
        driver.quit()
        return item
    item = initial_request()

    return item


if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
