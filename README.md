
# ETDLP - Microservicios

Portal de APIs a microservicios de ETDLP. Desde visitas hasta información de proveedores... lo que quieras, lo tenemos. 😎
## API Reference

#

#### Obtiene el historial partidario según DNI

```http
  GET /consulta_rop/{dni}
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `dni`      | `int` | **Required**. Retorna el historial partidario|

#

#### Obtiene la información de empresas proveedoras

```http
  GET /info_proveedores/{ruc}
```
| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `ruc` | `int` | **Required** Retorna información de la empresa  |

