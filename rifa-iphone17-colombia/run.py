import os
from app.main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print("=======================================================")
    print("🚀 PORTAL WEB SORTEO iPHONE 17 PRO (COLOMBIA)")
    print("=======================================================")
    print(f"🌐 Servidor escuchando en http://{host}:{port}")
    print("=======================================================")
    
    app.run(host=host, port=port, debug=False)
