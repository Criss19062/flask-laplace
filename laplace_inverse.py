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

        # Intentar resolver con el método directo de SymPy
        try:
            inversa = sp.inverse_laplace_transform(expresion, s, t)
            metodo_usado = "Método Directo de SymPy"
        except Exception as e:
            print(f" No se pudo hacer con el método directo: {e}")

            # Intentar resolver con Fracciones Parciales
            try:
                descomposicion = sp.apart(expresion, s)
                print(f" Método Usado: Fracciones Parciales")
                print(f" Expresión descompuesta: {descomposicion}")
                inversa = sp.inverse_laplace_transform(descomposicion, s, t)
                metodo_usado = "Fracciones Parciales"
            except Exception as e:
                print(f" No se pudo hacer fracciones parciales: {e}")

                # Si falla, usar Método Numérico
                print(f" Método Usado: Aproximación Numérica")
                inversa = sp.inverse_laplace_transform(expresion, s, t, noconds=True)
                metodo_usado = "Aproximación Numérica"

        # Intentar reescribir exponenciales y expandir trigonométricamente
        try:
            inversa = inversa.rewrite(sp.exp)
        except Exception as e:
            print(f"⚠️ Error en rewrite(sp.exp): {e}")

        # Si hay números complejos, aplicar la identidad de Euler
        if inversa.has(sp.I):
            try:
                inversa = inversa.expand(trig=True)
            except Exception as e:
                print(f"⚠️ Error en expand(trig=True): {e}")

        # Eliminar Heaviside(t) si aparece
        inversa = inversa.replace(sp.Heaviside(t), 1)

        print(f"✅ Resultado final ({metodo_usado}): {inversa}")
        return str(inversa)

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/laplace', methods=['GET'])
def calcular_laplace():
    expresion = request.args.get('expresion', "1 / (s + 1)")
    resultado = inversa_laplace(expresion)
    return jsonify({"resultado": resultado})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
