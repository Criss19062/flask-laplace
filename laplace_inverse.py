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

        inversa = None  # Variable para almacenar la solución final

        # Intentar resolver con el método directo de SymPy
        try:
            inversa = sp.inverse_laplace_transform(expresion, s, t)
            print(f"✅ Método Usado: Directo de SymPy")
        except Exception as e:
            print(f"⚠️ No se pudo hacer con el método directo: {e}")

        # Intentar resolver con Fracciones Parciales si el método directo falló
        if inversa is None:
            try:
                descomposicion = sp.apart(expresion, s)
                print(f"✅ Método Usado: Fracciones Parciales")
                print(f"🔹 Expresión descompuesta: {descomposicion}")
                inversa = sp.inverse_laplace_transform(descomposicion, s, t)
            except Exception as e:
                print(f"⚠️ No se pudo hacer fracciones parciales: {e}")

        # Si fracciones parciales también falló, usar método numérico
        if inversa is None:
            try:
                print(f"✅ Método Usado: Aproximación Numérica")
                inversa = sp.inverse_laplace_transform(expresion, s, t, noconds=True)

                # 🔹 Como último recurso, usar serie de Taylor
                if not inversa.has(t):  # Si SymPy no generó una función con 't'
                    inversa = sp.series(inversa, t, n=6).removeO()
            except Exception as e:
                print(f"⚠️ No se pudo calcular por ningún método: {e}")
                return "Error en el cálculo"

        # 🔹 Reemplazo final para mejorar la presentación
        inversa = inversa.replace(sp.Heaviside(t), 1)  # Evitar que aparezca Heaviside(t)
        inversa = sp.simplify(inversa.rewrite(sp.exp).expand(trig=True))  # Evitar números complejos

        return str(inversa)

    except Exception as e:
        return f"Error en la expresión ingresada: {str(e)}"

@app.route('/laplace', methods=['GET'])
def calcular_laplace():
    expresion = request.args.get('expresion', "1 / (s + 1)")
    resultado = inversa_laplace(expresion)
    return jsonify({"resultado": resultado})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

