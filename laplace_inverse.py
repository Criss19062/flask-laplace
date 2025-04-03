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

        # Método 1: Intentar la inversa de Laplace directa
        try:
            inversa = sp.inverse_laplace_transform(expresion, s, t)
            print(f"✅ Método Usado: Inversa de Laplace Directa")
        except Exception as e:
            print(f"⚠️ No se pudo hacer por método directo: {e}")

            # Método 2: Intentar con fracciones parciales
            try:
                descomposicion = sp.apart(expresion, s)
                print(f"✅ Método Usado: Fracciones Parciales")
                print(f"🔸 Expresión descompuesta: {descomposicion}")

                # Calcular la inversa de Laplace de cada término
                inversa = sp.inverse_laplace_transform(descomposicion, s, t)
            except Exception as e:
                print(f"⚠️ No se pudo hacer fracciones parciales: {e}")
                print(f"✅ Método Usado: Aproximación Numérica")
                inversa = sp.inverse_laplace_transform(expresion, s, t, noconds=True)

        # 🔹 Reemplazar Heaviside(t) por 1
        inversa = inversa.replace(sp.Heaviside(t), 1)

        # 🔹 Convertir números complejos en seno y coseno de otra manera
        inversa = sp.expand(inversa).simplify(trig=True)

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

