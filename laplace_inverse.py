from flask import Flask, request, jsonify
from flask_cors import CORS
import sympy as sp

app = Flask(__name__)
CORS(app)

s, t = sp.symbols('s t')

def inversa_laplace(expresion_str):
    try:
        expresion = sp.sympify(expresion_str) / s  # Aplicar escalón automáticamente
        print(f"\n🔹 Función recibida: {expresion_str}")
        print(f"🔹 Función con escalón aplicado: {expresion}")

        # Intentar resolver con Fracciones Parciales
        try:
            descomposicion = sp.apart(expresion, s)
            print(f" Método Usado: Fracciones Parciales")
            print(f" Expresión descompuesta: {descomposicion}")
            
            # Calcular la inversa de Laplace de cada término
            inversa = sp.inverse_laplace_transform(descomposicion, s, t)
            
            # Convierte números complejos en senos y cosenos
            inversa_simplificada = sp.simplify(inversa.rewrite(sp.Heaviside).rewrite(sp.exp).expand(trig=True))
            
            # Asegurar que solo la variable 's' se convierta en 't'
            inversa_simplificada = inversa_simplificada.subs(s, t)
            
            return str(inversa_simplificada)
        except Exception as e:
            print(f" No se pudo hacer fracciones parciales: {e}")
        
        # Si falla, usar Método Numérico
        print(f" Método Usado: Aproximación Numérica")
        inversa_numerica = sp.inverse_laplace_transform(expresion, s, t, noconds=True)
        return str(inversa_numerica)

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/laplace', methods=['GET'])
def calcular_laplace():
    expresion = request.args.get('expresion', "1 / (s + 1)")
    resultado = inversa_laplace(expresion)
    return jsonify({"resultado": resultado})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
