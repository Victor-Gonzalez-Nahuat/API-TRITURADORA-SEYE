import pymysql
import os
import datetime

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = int(os.getenv('DB_PORT'))

def expandir_rango_fechas(desde, hasta):
    """Ajusta el rango para que hasta incluya todo el día."""
    desde_dt = datetime.datetime.strptime(desde, '%Y-%m-%d')
    hasta_dt = datetime.datetime.strptime(hasta, '%Y-%m-%d') + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
    return desde_dt, hasta_dt


def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

def obtenerTotalesYDescuentos(desde_fecha, hasta_fecha, contribuyente=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            SUM(vt_efectivo) AS efectivo,
            SUM(vt_tarjeta) AS tarjeta,
            SUM(vt_credito) AS credito,
            SUM(vt_totalg) AS total_con_iva,
            SUM(vt_sub_total) AS total_sin_iva,
            SUM(vt_impuesto) AS iva
        FROM VEARMA01
        WHERE vt_bandera != '1' AND vt_fechat BETWEEN %s AND %s
    """, (desde_fecha, hasta_fecha))

    resultado = cursor.fetchone()
    conn.close()

    return {
        "efectivo": float(resultado[0] or 0),
        "tarjeta": float(resultado[1] or 0),
        "credito": float(resultado[2] or 0),
        "total_con_iva": float(resultado[3] or 0),
        "total_sin_iva": float(resultado[4] or 0),
        "iva": float(resultado[5] or 0)
    }



def obtenerRecibosConIntervaloYContribuyente(desde_fecha, hasta_fecha, contribuyente):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id_recibo, id_fecha, id_neto, id_descuento, id_concepto1, id_contribuyente 
        FROM TEARMO01 
        WHERE id_fecha BETWEEN %s AND %s
        AND id_contribuyente LIKE %s
        ORDER BY id_fecha DESC
    """, (desde_fecha, hasta_fecha, f"%{contribuyente}%"))

    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        return []

    recibos = [
        {
            "recibo": row[0],
            "fecha": row[1],
            "neto": row[2],
            "descuento": row[3],
            "concepto": row[4],
            "contribuyente": row[5],
        } 
        for row in resultados
    ]
    return recibos

def obtenerRecibosConIntervalo(desde_fecha, hasta_fecha):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_recibo, id_fecha, id_neto, id_descuento, id_concepto1, id_contribuyente 
        FROM TEARMO01 
        WHERE id_fecha BETWEEN %s AND %s
        ORDER BY id_fecha DESC
    """, (desde_fecha, hasta_fecha)) 

    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        return []

    recibos = [
        {
            "recibo": row[0],
            "fecha": row[1],
            "neto": row[2],
            "descuento": row[3],
            "concepto": row[4],
            "contribuyente": row[5],
        } 
        for row in resultados
    ]
    return recibos

def obtenerRecibosHoy():
    conn = get_connection()
    cursor = conn.cursor()

    fecha_hoy = datetime.datetime.today().strftime('%y%m%d')

    cursor.execute("""
        SELECT id_recibo, id_fecha, id_neto, id_descuento, id_concepto1, id_contribuyente 
        FROM TEARMO01 
        WHERE id_fecha = %s
        ORDER BY id_fecha DESC
    """, (fecha_hoy,)) 

    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        return []

    recibos = [
        {
            "recibo": row[0],
            "fecha": row[1],
            "neto": row[2],
            "descuento": row[3],
            "concepto": row[4],
            "contribuyente": row[5],
        } 
        for row in resultados
    ]
    return recibos

def obtenerDespliegueTotales(desde_fecha, hasta_fecha):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            c.id_nombrecuenta,
            COALESCE(SUM(m.id_neto), 0) AS total_neto,
            COALESCE(SUM(m.id_descuento), 0) AS total_descuento
        FROM TEARMO01 m
        JOIN TEARCA01 c ON m.id_cuenta = c.id_codigoc
        WHERE m.id_fecha BETWEEN %s AND %s
        AND m.id_status = 0
        GROUP BY c.id_nombrecuenta
        ORDER BY c.id_nombrecuenta
    """, (desde_fecha, hasta_fecha))

    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        return []

    despliegue = [
        {
            "cuenta": row[0],  # Ahora es el nombre de la cuenta
            "total_neto": float(row[1]),
            "total_descuento": float(row[2])
        } 
        for row in resultados
    ]
    return despliegue
