from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import sympy as sp

app = Flask(__name__)
CORS(app,resources={r"/*": {"origins": ["*", "null"]}})

# Ruta ligera para UptimeRobot
@app.route('/')
def home():
    return '🟢 API de Laplace activa'

@app.route('/ping')
def ping():
    return 'pong'

s, t = sp.symbols('s t')

def filtrar_numeros_pequenos(expresion, umbral=1e-10):
    """Reemplaza números muy pequeños por 0 para evitar términos insignificantes en la respuesta."""
    return expresion.xreplace({n: 0 for n in expresion.atoms(sp.Number) if abs(n) < umbral})

def aplicar_identidad_euler(expresion):
    """Convierte cualquier número complejo en términos de senos y cosenos usando la Identidad de Euler"""
    # Buscar exponenciales complejas
    expresion = expresion.expand()  # Expandir para asegurarse de que las exponenciales estén separadas

    for termino in expresion.atoms(sp.exp):  # Buscar términos de la forma e^(algo)
        argumento = termino.args[0]  # Extraer el exponente
        if argumento.has(sp.I):  # Si tiene parte imaginaria
            a, b = sp.re(argumento), sp.im(argumento)  # Separar parte real e imaginaria
            nueva_exp = sp.exp(a*t) * (sp.cos(b*t) + sp.I * sp.sin(b*t))  # Aplicar Euler
            expresion = expresion.subs(termino, nueva_exp)  # Reemplazar en la ecuación

    return sp.simplify(expresion)

def inversa_laplace(expresion_str):
    try:
        expresion = sp.sympify(expresion_str) / s  # Aplicar escalón automáticamente
        print(f"\n🔹 Función recibida: {expresion_str}")
        print(f"🔹 Función con escalón aplicado: {expresion}")

        # 🔴 Intentar con el método por defecto de SymPy
        try:
            inversa = sp.inverse_laplace_transform(expresion, s, t)
            print(f"✅ Método Usado: Inversa Directa de SymPy")
        except Exception as e:
            print(f"❌ No se pudo hacer con SymPy directamente: {e}")
        else:
            inversa = aplicar_identidad_euler(inversa)  # Forzar conversión manual
            inversa = filtrar_numeros_pequenos(inversa)
            return str(inversa).replace("Heaviside(t)", "1")
        
        # 🟠 Intentar con Fracciones Parciales
        try:
            descomposicion = sp.apart(expresion, s)
            print(f"✅ Método Usado: Fracciones Parciales")
            print(f"🛠 Expresión descompuesta: {descomposicion}")
            inversa = sp.inverse_laplace_transform(descomposicion, s, t)
        except Exception as e:
            print(f"❌ No se pudo hacer con Fracciones Parciales: {e}")
        else:
            inversa = aplicar_identidad_euler(inversa)  # Forzar conversión manual
            inversa = filtrar_numeros_pequenos(inversa)
            return str(inversa).replace("Heaviside(t)", "1")
            
        # 🟡 Último recurso: Método Numérico
        print(f"⚠️ Método Usado: Aproximación Numérica")
        inversa = sp.inverse_laplace_transform(expresion, s, t, noconds=True)
        inversa = aplicar_identidad_euler(inversa)  # Forzar conversión manual
        inversa = filtrar_numeros_pequenos(inversa)
        return str(inversa).replace("Heaviside(t)", "1")

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/laplace', methods=['GET'])
def calcular_laplace():
    expresion = request.args.get('expresion', "1 / (s + 1)")
    resultado = inversa_laplace(expresion)
    return jsonify({"resultado": resultado})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
