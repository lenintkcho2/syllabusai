import psycopg2
from sqlalchemy import create_engine, text

def test_new_user():
    try:
        print("🔍 Probando conexión con usuario testuser...")
        
        # Conexión directa
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="syllabusai_db",
            user="testuser",
            password="test123"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT current_user, current_database();")
        result = cursor.fetchone()
        print(f"✅ Conexión exitosa!")
        print(f"Usuario: {result[0]}, Base de datos: {result[1]}")
        
        cursor.close()
        conn.close()
        
        # Probar SQLAlchemy
        print("\n🔍 Probando SQLAlchemy...")
        url = "postgresql://testuser:test123@localhost:5432/syllabusai_db"
        engine = create_engine(url)
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            print("✅ SQLAlchemy funciona!")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    if test_new_user():
        print("\n🎉 ¡Perfecto! Actualiza tu .env con:")
        print("DATABASE_URL=postgresql://testuser:test123@localhost:5432/syllabusai_db")
    else:
        print("\n❌ Aún hay problemas. Revisar configuración de pgAdmin.")