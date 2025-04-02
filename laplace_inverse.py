from flask_cors import CORS
from flask import Flask, request, jsonify
import sympy as sp
import scipy.signal as sig
import numpy as np

app = Flask(__name__)
CORS(app)

# Definir variables simbólicas
s, t = sp.symbols('s t')

def inversa_laplace(expresion_str):
    try:
        expresion = sp.sympify(expresion_str)

        # Intentar fracciones parciales
        fracciones = sp.apart(expresion, s)
        
        # Resolver coeficientes con sistema de ecuaciones
        coeficientes = sp.symbols(f'a:{len(fracciones.args)}')  # Variables para coeficientes
        ecuaciones = [sp.expand(f - fracciones) for f in coeficientes]
        soluciones = sp.solve(ecuaciones, coeficientes)
        
        # Reemplazar coeficientes en la expresión
        expresion_temporal = sum(soluciones[c] * sp.exp(-p * t) for c, p in zip(coeficientes, fracciones.args))
        
        return str(expresion_temporal)

    except Exception:
        try:
            # Método numérico si fracciones parciales falla
            num, den = sp.fraction(sp.sympify(expresion_str))
            num = [float(c) for c in sp.Poly(num, s).all_coeffs()]
            den = [float(c) for c in sp.Poly(den, s).all_coeffs()]

            sistema = sig.TransferFunction(num, den)  # Crear sistema
            t_vals, y_vals = sig.step(sistema)  # Respuesta al escalón
            
            # Convertir a expresión simbólica aproximada
            expr_numerica = sum(y * sp.Heaviside(t - tau) for tau, y in zip(t_vals, y_vals))
            
            return str(expr_numerica)
        except Exception as e:
            return f"Error: No se pudo calcular analíticamente ni numéricamente. {str(e)}"

@app.route('/laplace', methods=['GET'])
def calcular_laplace():
    expresion = request.args.get('expresion', "1 / (s + 1)")
    resultado = inversa_laplace(expresion)
    return jsonify({"resultado": resultado})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
