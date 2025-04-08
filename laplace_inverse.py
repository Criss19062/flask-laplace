from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import sympy as sp
from mpmath import invertlaplace, mp, mpc, mpf
import numpy as np

app = Flask(__name__)
CORS(app) # Esto permite solicitudes desde cualquier origen

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

mp.dps = 15
def inversa_laplace(expresion_str):
    try:
        expresion = sp.sympify(expresion_str) / s  # Aplicar escalón automáticamente
        print(f"\n🔹 Función recibida: {expresion_str}")
        print(f"🔹 Función con escalón aplicado: {expresion}")
        
        # 🟠 Intentar con Fracciones Parciales
        try:
            descomposicion = sp.apart(expresion, s)
            print(f"✅ Método Usado: Fracciones Parciales")
            print(f"🛠 Expresión descompuesta: {descomposicion}")
            inversa = sp.inverse_laplace_transform(descomposicion, s, t)
        except Exception as e:
            print(f"❌ Fracciones Parciales fallaron: {e}")
        
            # 🟡 Intentar con noconds=True
            try:
                inversa = sp.inverse_laplace_transform(expresion, s, t, noconds=True)
                print(f"✅ Método Usado: noconds=True")
            except Exception as e:
                print(f"⚠️ SymPy tampoco pudo (noconds=True): {e}")
        
                # 🔴 Último Recurso: Método Numérico con mpmath
                print(f"⚠️ Usando mpmath.invertlaplace como último recurso...")
        
                def laplace_func(s_num):
                    try:
                        f = sp.lambdify(s, expresion, modules=["mpmath", "numpy"])
                        return f(s_num)
                    except Exception as inner_e:
                        print(f"Error al convertir con lambdify: {inner_e}")
                        return 0
        
                try:
                    # Probar en algunos valores de t para verificar que funciona
                    valores_t = np.linspace(0.01, 10, 100)
                    resultado_numerico = [float(invertlaplace(laplace_func, ti)) for ti in valores_t]
                    resultado_t = list(map(float, valores_t))
                    print(f"✅ Método Usado: mpmath.invertlaplace")
                    # Devolver como dos listas separadas
                    return {
                        "t": resultado_t,
                        "y": resultado_numerico,
                        "metodo": "numérico"
                    }
                    
                except Exception as final_e:
                    return f"Error en método numérico (mpmath): {str(final_e)}"
        
        inversa = aplicar_identidad_euler(inversa)
        inversa = filtrar_numeros_pequenos(inversa)
        return str(inversa).replace("Heaviside(t)", "1")

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/laplace', methods=['GET'])
@cross_origin(origin="*")  # <- esto permite peticiones de GitHub Pages
def calcular_laplace():
    expresion = request.args.get('expresion', "1 / (s + 1)")
    resultado = inversa_laplace(expresion)
    return jsonify({"resultado": resultado})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
