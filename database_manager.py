from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import pymysql
import pymssql
from pymongo import MongoClient
import sqlite3
import redis
import json
from neo4j import GraphDatabase
try:
    from cassandra.cluster import Cluster
    from cassandra.auth import PlainTextAuthProvider
except ImportError:
    Cluster = None

class BaseDeDatos(ABC):
    """
    El contrato de la base de datos ahora exige recibir credenciales dinámicas
    y la capacidad de introspeccionar su propio esquema para alimentar la UI.
    """
    def __init__(self, credenciales: Dict[str, Any]):
        self.credenciales = credenciales

    @abstractmethod
    def conectar(self):
        pass

    @abstractmethod
    def obtener_esquema(self) -> Dict[str, List[str]]:
        """ Devuelve un diccionario { "nombre_tabla": ["col1", "col2"] } """
        pass

    @abstractmethod
    def ejecutar_consulta(self, query_o_filtro: Union[str, Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        pass

class PostgresDB(BaseDeDatos):
    def conectar(self):
        return psycopg2.connect(
            host=self.credenciales.get('host'),
            port=int(self.credenciales.get('port', 5432)),
            user=self.credenciales.get('user'),
            password=self.credenciales.get('password'),
            dbname=self.credenciales.get('database'),
            cursor_factory=RealDictCursor
        )

    def obtener_esquema(self) -> Dict[str, List[str]]:
        esquema = {}
        query = """
            SELECT table_name, column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public'
        """
        resultados = self.ejecutar_consulta(query)
        for fila in resultados:
            t_name = fila['table_name']
            c_name = fila['column_name']
            if t_name not in esquema: esquema[t_name] = []
            esquema[t_name].append(c_name)
        return {"tablas": esquema}

    def ejecutar_consulta(self, query_o_filtro: str, **kwargs) -> List[Dict[str, Any]]:
        with self.conectar() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_o_filtro)
                if cursor.description: return [dict(row) for row in cursor.fetchall()]
                return []

class MySQLDB(BaseDeDatos):
    def conectar(self):
        try:
            return pymysql.connect(
                host=self.credenciales.get('host'),
                port=int(self.credenciales.get('port', 3306)),
                user=self.credenciales.get('user'),
                password=self.credenciales.get('password'),
                database=self.credenciales.get('database'),
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=5
            )
        except pymysql.MySQLError as e:
            raise ConnectionError(f"MySQL connection error: {e}")

    def obtener_esquema(self) -> Dict[str, List[str]]:
        esquema = {}
        db = self.credenciales.get('database')
        query = f"SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = '{db}'"
        resultados = self.ejecutar_consulta(query)
        for fila in resultados:
            t_name = fila.get('table_name') or fila.get('TABLE_NAME')
            c_name = fila.get('column_name') or fila.get('COLUMN_NAME')
            if t_name not in esquema: esquema[t_name] = []
            esquema[t_name].append(c_name)
        return {"tablas": esquema}

    def ejecutar_consulta(self, query_o_filtro: str, **kwargs) -> List[Dict[str, Any]]:
        conexion = self.conectar()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(query_o_filtro)
                if cursor.description: return cursor.fetchall()
                conexion.commit()
                return []
        finally:
            conexion.close()

class SQLiteDB(BaseDeDatos):
    def conectar(self):
        db_path = self.credenciales.get('database', 'local_monitor.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def obtener_esquema(self) -> Dict[str, List[str]]:
        esquema = {}
        tablas = self.ejecutar_consulta("SELECT name FROM sqlite_master WHERE type='table'")
        for t in tablas:
            t_name = t['name']
            cols = self.ejecutar_consulta(f"PRAGMA table_info({t_name})")
            esquema[t_name] = [c['name'] for c in cols]
        return {"tablas": esquema}

    def ejecutar_consulta(self, query_o_filtro: str, **kwargs) -> List[Dict[str, Any]]:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(query_o_filtro)
            if cursor.description: return [dict(row) for row in cursor.fetchall()]
            conn.commit()
            return []

class SQLServerDB(BaseDeDatos):
    def conectar(self):
        try:
            return pymssql.connect(
                server=self.credenciales.get('host'),
                port=str(self.credenciales.get('port', 1433)),
                user=self.credenciales.get('user'),
                password=self.credenciales.get('password'),
                database=self.credenciales.get('database'),
                as_dict=True,
                timeout=5
            )
        except pymssql._mssql.MssqlException as e:
            raise ConnectionError(f"SQL Server connection error: {e}")

    def obtener_esquema(self) -> Dict[str, List[str]]:
        esquema = {}
        query = "SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS"
        resultados = self.ejecutar_consulta(query)
        for fila in resultados:
            t_name = fila['TABLE_NAME']
            c_name = fila['COLUMN_NAME']
            if t_name not in esquema: esquema[t_name] = []
            esquema[t_name].append(c_name)
        return {"tablas": esquema}

    def ejecutar_consulta(self, query_o_filtro: str, **kwargs) -> List[Dict[str, Any]]:
        conexion = self.conectar()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(query_o_filtro)
                if cursor.description: return cursor.fetchall()
                conexion.commit()
                return []
        finally:
            conexion.close()

class MongoDB(BaseDeDatos):
    def conectar(self):
        # Para MongoDB, el usuario puede proveer URI directa o Host
        uri = self.credenciales.get('host', 'mongodb://localhost:27017/') 
        return MongoClient(uri)

    def obtener_esquema(self) -> Dict[str, List[str]]:
        esquema = {}
        cliente = self.conectar()
        try:
            db_name = self.credenciales.get('database')
            db = cliente[db_name]
            colecciones = db.list_collection_names()
            # Muestreo rápido de esquema
            for col_name in colecciones:
                doc = db[col_name].find_one()
                esquema[col_name] = list(doc.keys()) if doc else []
            return {"tablas": esquema}
        finally:
            cliente.close()

    def ejecutar_consulta(self, query_o_filtro: Dict[str, Any], coleccion: str = None, limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        if not coleccion: raise ValueError("MongoDB requiere 'coleccion'")
        cliente = self.conectar()
        try:
            db_name = self.credenciales.get('database')
            col = cliente[db_name][coleccion]
            resultados = list(col.find(query_o_filtro).limit(limit))
            for doc in resultados:
                if '_id' in doc: doc['_id'] = str(doc['_id'])
            return resultados
        finally:
            cliente.close()

class RedisDB(BaseDeDatos):
    def conectar(self):
        db_val = self.credenciales.get('database', 0)
        try:
            db_num = int(db_val)
        except (ValueError, TypeError):
            db_num = 0
        
        host = self.credenciales.get('host', 'localhost')
        port = int(self.credenciales.get('port', 6379))
        password = self.credenciales.get('password') or None
        
        ssl_ports = [6380, 18812, 18813]
        use_ssl = self.credenciales.get('ssl', False) or port in ssl_ports
        
        return redis.Redis(
            host=host,
            port=port,
            db=db_num,
            password=password,
            decode_responses=True,
            ssl=use_ssl
        )

    def obtener_esquema(self) -> Dict[str, List[str]]:
        cliente = self.conectar()
        try:
            muestra = cliente.keys("*")[:5]
            esquema = {"redis_store": ["valor"]}
            if muestra:
                val = cliente.get(muestra[0])
                try:
                    obj = json.loads(val)
                    if isinstance(obj, dict): esquema["redis_store"] = list(obj.keys())
                except: pass
            return {"tablas": esquema}
        finally:
            cliente.close()

    def ejecutar_consulta(self, query_o_filtro: str, tipo_comando: str = "get", **kwargs) -> List[Dict[str, Any]]:
        cliente = self.conectar()
        try:
            if tipo_comando.lower() == "get":
                valor = cliente.get(query_o_filtro)
                try:
                    parsed = json.loads(valor) if valor else None
                    if isinstance(parsed, dict): return [parsed]
                except:
                    parsed = valor
                return [{"llave": query_o_filtro, "valor": parsed}]
            elif tipo_comando.lower() == "hgetall":
                return [cliente.hgetall(query_o_filtro)]
            return []
        finally:
            cliente.close()

class Neo4jDB(BaseDeDatos):
    def conectar(self):
        return GraphDatabase.driver(
            self.credenciales.get('host'), 
            auth=(self.credenciales.get('user'), self.credenciales.get('password'))
        )

    def obtener_esquema(self) -> Dict[str, List[str]]:
        driver = self.conectar()
        try:
            with driver.session() as session:
                result = session.run("MATCH (n) RETURN labels(n) AS labels, keys(n) AS properties LIMIT 5")
                esquema = {}
                for record in result:
                    labels, props = record["labels"], record["properties"]
                    if labels:
                        lbl = labels[0]
                        if lbl not in esquema: esquema[lbl] = []
                        esquema[lbl] = list(set(esquema[lbl] + props))
            return {"tablas": esquema}
        finally:
            driver.close()

    def ejecutar_consulta(self, query_o_filtro: str, parametros: Dict[str, Any] = None, **kwargs) -> List[Dict[str, Any]]:
        driver = self.conectar()
        try:
            with driver.session() as session:
                result = session.run(query_o_filtro, parameters=parametros or {})
                lista = []
                for record in result:
                    d = dict(record)
                    plana = {}
                    for k, v in d.items():
                        if hasattr(v, "items"): plana.update(dict(v.items()))
                        else: plana[k] = v
                    lista.append(plana)
                return lista
        finally:
            driver.close()

class CassandraDB(BaseDeDatos):
    def conectar(self):
        if Cluster is None:
            raise ImportError("El paquete 'cassandra-driver' no está instalado.")
        auth_provider = None
        if self.credenciales.get('user') and self.credenciales.get('password'):
            auth_provider = PlainTextAuthProvider(
                username=self.credenciales.get('user'),
                password=self.credenciales.get('password')
            )
        cluster = Cluster(
            contact_points=[self.credenciales.get('host', 'localhost')],
            port=int(self.credenciales.get('port', 9042)),
            auth_provider=auth_provider
        )
        return cluster.connect(self.credenciales.get('database'))

    def obtener_esquema(self) -> Dict[str, List[str]]:
        esquema = {}
        session = self.conectar()
        try:
            from cassandra.query import SimpleStatement
            query = "SELECT table_name, column_name FROM system_schema.columns WHERE keyspace_name = %s"
            rows = session.execute(SimpleStatement(query), [self.credenciales.get('database')])
            for row in rows:
                t_name = row.table_name
                c_name = row.column_name
                if t_name not in esquema:
                    esquema[t_name] = []
                esquema[t_name].append(c_name)
        finally:
            session.cluster.shutdown()
        return {"tablas": esquema}

    def ejecutar_consulta(self, query_o_filtro: str, params: Any = None, **kwargs) -> List[Dict[str, Any]]:
        session = self.conectar()
        try:
            from cassandra.query import SimpleStatement
            stmt = SimpleStatement(query_o_filtro)
            rows = session.execute(stmt, params or [])
            return [row._asdict() for row in rows]
        finally:
            session.cluster.shutdown()


class DatabaseFactory:
    @staticmethod
    def obtener_motor(motor: str, credenciales: Dict[str, Any]) -> BaseDeDatos:
        motores = {
            "postgres": PostgresDB, "mysql": MySQLDB, "sqlserver": SQLServerDB,
            "sqlite": SQLiteDB, "mongodb": MongoDB, "redis": RedisDB, "neo4j": Neo4jDB,
            "mariadb": MySQLDB, "cassandra": CassandraDB
        }
        clase = motores.get(motor.lower())
        if not clase: raise ValueError(f"Motor '{motor}' no soportado.")
        return clase(credenciales)


def _es_motor_sql(motor: BaseDeDatos) -> bool:
    return isinstance(motor, (PostgresDB, MySQLDB, SQLiteDB, SQLServerDB))


def _quote_identifier_sql(motor: BaseDeDatos, nombre: str) -> str:
    if isinstance(motor, SQLServerDB):
        return f"[{nombre}]"
    if isinstance(motor, MySQLDB):
        return f"`{nombre}`"
    return f'"{nombre}"'



def obtener_filas_tabla(motor: BaseDeDatos, tabla: str, limite: int = 100) -> List[Dict[str, Any]]:
    if isinstance(motor, MongoDB):
        return motor.ejecutar_consulta({}, coleccion=tabla, limit=limite)
    if isinstance(motor, RedisDB):
        return motor.ejecutar_consulta(tabla)
    if isinstance(motor, Neo4jDB):
        consulta = f"MATCH (n:{tabla}) RETURN n LIMIT {limite}"
        return motor.ejecutar_consulta(consulta)

    if isinstance(motor, SQLiteDB):
        return motor.ejecutar_consulta(f'SELECT * FROM "{tabla}" LIMIT {limite}')
    if isinstance(motor, SQLServerDB):
        return motor.ejecutar_consulta(f"SELECT TOP {limite} * FROM {_quote_identifier_sql(motor, tabla)}")
    return motor.ejecutar_consulta(f'SELECT * FROM {_quote_identifier_sql(motor, tabla)} LIMIT {limite}')


def obtener_valor_ejemplo(motor: BaseDeDatos, tabla: str, columna: str) -> Optional[Any]:
    filas = obtener_filas_tabla(motor, tabla, limite=25)
    for fila in filas:
        if columna in fila and fila[columna] is not None:
            return fila[columna]
    return None


def transformar_columna_tabla(
    motor: BaseDeDatos,
    tabla: str,
    columna: str,
    transformador,
    limite: int = 1000,
) -> int:
    filas = obtener_filas_tabla(motor, tabla, limite=limite)
    if not filas:
        return 0

    actualizados = 0

    if isinstance(motor, MongoDB):
        cliente = motor.conectar()
        try:
            db_name = motor.credenciales.get('database')
            col = cliente[db_name][tabla]
            valores_vistos = set()
            for fila in filas:
                valor_actual = fila.get(columna)
                valor_key = repr(valor_actual)
                if valor_actual is None or valor_key in valores_vistos:
                    continue
                valores_vistos.add(valor_key)
                nuevo_valor = transformador(valor_actual)
                if nuevo_valor == valor_actual:
                    continue
                resultado = col.update_many({columna: valor_actual}, {"$set": {columna: nuevo_valor}})
                actualizados += int(resultado.modified_count or 0)
        finally:
            cliente.close()
        return actualizados

    if isinstance(motor, RedisDB):
        cliente = motor.conectar()
        try:
            valor_actual = cliente.get(tabla)
            if valor_actual is None:
                valor_actual = cliente.hgetall(tabla)
                if isinstance(valor_actual, dict) and columna in valor_actual:
                    nuevo_valor = transformador(valor_actual[columna])
                    if nuevo_valor != valor_actual[columna]:
                        cliente.hset(tabla, columna, nuevo_valor)
                        return 1
                return 0

            nuevo_valor = transformador(valor_actual)
            if nuevo_valor != valor_actual:
                cliente.set(tabla, nuevo_valor)
                return 1
            return 0
        finally:
            cliente.close()

    if isinstance(motor, Neo4jDB):
        driver = motor.conectar()
        try:
            with driver.session() as session:
                query = f"MATCH (n:{tabla}) WHERE n.{columna} IS NOT NULL RETURN DISTINCT n.{columna} AS valor LIMIT {limite}"
                valores = [registro.get("valor") for registro in session.run(query)]
                for valor_actual in valores:
                    nuevo_valor = transformador(valor_actual)
                    if nuevo_valor == valor_actual:
                        continue
                    session.run(
                        f"MATCH (n:{tabla}) WHERE n.{columna} = $valor_actual SET n.{columna} = $nuevo_valor",
                        valor_actual=valor_actual,
                        nuevo_valor=nuevo_valor,
                    )
                    actualizados += 1
        finally:
            driver.close()
        return actualizados

    conn = motor.conectar()
    try:
        cursor = conn.cursor()
        if isinstance(motor, SQLiteDB):
            placeholder = "?"
        else:
            placeholder = "%s"

        valores_vistos = set()
        tabla_sql = _quote_identifier_sql(motor, tabla)
        columna_sql = _quote_identifier_sql(motor, columna)
        for fila in filas:
            valor_actual = fila.get(columna)
            valor_key = repr(valor_actual)
            if valor_actual is None or valor_key in valores_vistos:
                continue
            valores_vistos.add(valor_key)
            try:
                valor_como_str = str(valor_actual) if not isinstance(valor_actual, str) else valor_actual
                nuevo_valor = transformador(valor_como_str)
            except Exception:
                continue
            if nuevo_valor == valor_actual:
                continue
            cursor.execute(
                f"UPDATE {tabla_sql} SET {columna_sql} = {placeholder} WHERE {columna_sql} = {placeholder}",
                (nuevo_valor, valor_actual),
            )
            actualizados += max(int(getattr(cursor, "rowcount", 0) or 0), 0)
        conn.commit()
        return actualizados
    finally:
        conn.close()
