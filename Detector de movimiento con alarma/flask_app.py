from flask import Flask, request, jsonify, render_template_string
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import pytz  # Esta biblioteca es para poder modificar correctamente el formato de la fecha y hora

app = Flask(__name__)

# Función para crear la conexión a la base de datos
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host="servidormysql.com",  # Aquí va la IP del servidor MySQL
            user="usuario",  # Usuario MySQL
            password="contraseña",  # Contraseña MySQL
            database="seguridad"  # Nombre de la base de datos
        )
    except Error as e:
        print(f"Error al conectar con la base de datos: {e}")
    return connection

@app.route('/')
def hello_world():
    return 'Hello from Flask!'


# Ruta para insertar datos en la base de datos
@app.route('/insert', methods=['POST'])
def insert_data():
    data = request.get_json()
    descripcion = data.get('descripcion')

    if descripcion:
        try:
            # Obtener la hora actual en la zona horaria de Argentina
            tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
            argentina_time = datetime.now(tz_argentina)  # Hora de Argentina

            # Crear conexión a la base de datos
            connection = create_connection()
            if connection.is_connected():
                cursor = connection.cursor()
                sql_query = "INSERT INTO movimientos (timestamp, descripcion) VALUES (%s, %s)"
                cursor.execute(sql_query, (argentina_time, descripcion))  # Guardar hora en formato argentino
                connection.commit()
                cursor.close()
                connection.close()
                return jsonify({"status": "success", "message": "Movimiento registrado"}), 200
        except Error as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        return jsonify({"status": "error", "message": "Datos inválidos"}), 400


# Ruta para mostrar los registros en formato HTML con tabla y CSS
@app.route('/records', methods=['GET'])
def show_records():
    try:
        connection = create_connection()
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT id, timestamp, descripcion FROM movimientos")
            records = cursor.fetchall()
            cursor.close()
            connection.close()

            # Formatear los registros
            formatted_records = []
            for record in records:
                formatted_timestamp = record[1].strftime('%d/%m/%Y %H:%M:%S')  # Formato deseado: día/mes/año hora:minuto:segundo
                formatted_records.append((record[0], formatted_timestamp, record[2]))

            # HTML para mostrar la tabla
            html_template = '''
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Registros de Movimientos</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f9;
                        color: #333;
                        margin: 0;
                        padding: 20px;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin: 25px 0;
                        font-size: 18px;
                        text-align: left;
                        box-shadow: 0 2px 3px rgba(0,0,0,0.1);
                    }
                    th, td {
                        padding: 12px;
                        border-bottom: 1px solid #ddd;
                    }
                    th {
                        background-color: #333;
                        color: #fff;
                        cursor: pointer;
                    }
                    th.sortable:hover {
                        background-color: #555;
                    }
                    tr:nth-child(even) {
                        background-color: #f2f2f2;
                    }
                    h2 {
                        text-align: center;
                    }
                </style>
            </head>
            <body>
                <h2>Registros de Movimientos</h2>
                <table>
                    <thead>
                        <tr>
                            <th class="sortable" onclick="sortTable(0)">ID</th>
                            <th class="sortable" onclick="sortTable(1)">Fecha y Hora</th>
                            <th class="sortable" onclick="sortTable(2)">Descripción</th>
                        </tr>
                    </thead>
                    <tbody id="records-body">
                        {% for record in records %}
                        <tr>
                            <td>{{ record[0] }}</td>
                            <td>{{ record[1] }}</td> <!-- Timestamp ya formateado -->
                            <td>{{ record[2] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>


                <script>
                    // Función para ordenar las columnas al hacer clic en el encabezado
                    function sortTable(columnIndex) {
                        const table = document.querySelector('table');
                        const tbody = table.querySelector('tbody');
                        const rows = Array.from(tbody.querySelectorAll('tr'));
                        let isAscending = table.dataset.sortDirection === 'ascending';

                        // Ordenar las filas
                        rows.sort((rowA, rowB) => {
                            const cellA = rowA.querySelectorAll('td')[columnIndex].textContent.trim();
                            const cellB = rowB.querySelectorAll('td')[columnIndex].textContent.trim();

                            if (columnIndex === 1) {
                                // Para la columna de fecha/hora, convertir a Date
                                return isAscending
                                    ? new Date(cellA) - new Date(cellB)
                                    : new Date(cellB) - new Date(cellA);
                            } else {
                                // Para las otras columnas, comparar como texto
                                return isAscending
                                    ? cellA.localeCompare(cellB, 'es', { numeric: true })
                                    : cellB.localeCompare(cellA, 'es', { numeric: true });
                            }
                        });

                        // Actualizar el orden en el DOM
                        rows.forEach(row => tbody.appendChild(row));

                        // Cambiar la dirección de ordenamiento para la próxima vez
                        table.dataset.sortDirection = isAscending ? 'descending' : 'ascending';
                    }
                </script>
            </body>
            </html>
            '''

            return render_template_string(html_template, records=formatted_records), 200

    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Iniciar la aplicación
  if __name__ == '__main__':
    app.run(debug=True)

