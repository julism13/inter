# TP1 - Redes 
- **Cátedra:** Alvarez Hamelin - $01$ (martes)
- **Cuatrimestre:** $1\text{C}$ $2026$
- **Grupo:** 16

## Integrantes
- Leandro Elias Brizuela - $109842$
- José Rafael Patty Morales - $109843$
- Ivan Fuschetto - $110632$
- Julianna Sanchez - $109621$ 
- Dulcinea Fernández - $110182$

# ¿Cómo ejecutar el programa?
Una vez descargado, ubicarse en la carpeta `src` del proyecto.

## Servidor
Para poder levantar el **servidor** se deberá mandar por línea de comandos la siguiente estructura de comando:

`start - server [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [- s DIRPATH ]`

Descripción de los argumentos:

```
-h : -- help, mostrar este mensaje de ayuda y salir.
-v : -- verbose, aumentar la verbosidad de la salida.
-q : -- quiet, disminuir la verbosidad de la salida.
-H : -- host, dirección IP del servidor.
-p : -- port, puerto del servidor.
-s : -- storage, ruta del directorio de almacenamiento.
```

Por ejemplo, si queremos levantar un **servidor** en $0.0.0.0$, en el puerto $1234$ y que la ruta del directorio de almacenamiento sea `./archivos` el comando sería:

```
python3 start-server.py -H 0.0.0.0 -p 8080 -s ./archivos_servidor -v
```

## Cliente
El cliente puede realizar operaciones tanto de **subida** (**upload**) o de **bajada** (**download**). 
 
 
### Upload
Para poder levantar un **cliente** y que pueda **subir información** al **servidor** se debera mandar por línea de comandos la siguiente estructura de comando:

`upload [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - s FILEPATH ] [ - n FILENAME ] [ - r protocol ]`

Descripción de los argumentos:

```
-h , -- help, mostrar este mensaje de ayuda y salir.
-v , -- verbose, aumentar la verbosidad de la salida.
-q , -- quiet, disminuir la verbosidad de la salida.
-H , -- host, dirección IP del servidor.
-p , -- port, puerto del servidor.
-s , -- src, ruta del archivo fuente.
-n , -- name, nombre del archivo, con el que se guardara en el servidor.
-r , -- protocol, protocolo de recuperación de errores. 
```
Por ejemplo, si queremos levantar un **cliente**, para que pueda subir el archivo `ejemplo.txt`, usando el protocolo `stop and wait`, en la IP $0.0.0.0$ y puerto $1234$ pertenecientes al servidor y que en el servidor se almacene con el nombre `ejemplo_servidor.txt` el comando sería:

```
python3 upload.py -H 0.0.0.0 -p 1234 -s ejemplo.txt -n .ejemplo_servidor.txt -r stop_and_wait -v
```

Teniendo el mismo ejemplo pero con `selective repeat` el comando sería:

```
python3 upload.py -H 0.0.0.0 -p 1234 -s ejemplo.txt -n .ejemplo_servidor.txt -r stop_and_wait -v
```
**Disclaimer:** El archivo que se quiere subir al servidor, debe existir previemante para realice la operación.

### Download
Para poder levantar un **cliente** y que pueda **bajar información** del servidor se debera mandar por la línea de comandos la siguiente estructura de comando:

`download [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - d FILEPATH ] [ - n FILENAME ] [ - r protocol ]`

Descripción de los argumentos:

```
-h , -- help, mostrar este mensaje de ayuda y salir.
-v , -- verbose, aumentar la verbosidad de la salida.
-q , -- quiet, disminuir la verbosidad de la salida.
-H , -- host, dirección IP del servidor.
-p , -- port, puerto del servidor.
-d , -- dst, ruta del archivo de destino.
-n , -- name, nombre del archivo, con el que se guardara en local.
-r , -- protocol protocolo de recuperación de errores.
```

Por ejemplo, si queremos levantar un **cliente**, para que pueda bajar un archivo `ejemplo.txt`, usando el protocolo `stop and wait`, en la IP $0.0.0.0$ y puerto $1234$ pertenecientes al servidor y que en local se almacene con el nombre `ejemplo_local.txt` el comando sería:

```
python3 download.py -H 0.0.0.0 -p 1234 -d ejemplo.txt -n ejemplo_local.txt -r stop_and_wait -v 
```

Teniendo el mismo ejemplo pero con `selective repeat` el comando sería:

```
python3 download.py -H 0.0.0.0 -p 1234 -d ejemplo.txt -n ejemplo_local.txt -r selective_repeat -v 
```
**Disclaimer:** El archivo que se quiere bajar del **servidor**, debe existir previemante para que se realice la operación.

## Verificación de codificación PEP8
Se deberán correr el siguiente comando:
```
flake8 .
```

