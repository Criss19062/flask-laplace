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

        # Intentar resolver directamente con SymPy
        try:
            inversa = sp.inverse_laplace_transform(expresion, s, t)
            inversa = sp.simplify(inversa.expand(trig=True))  # Expandir en términos trigonométricos
            print(f" Método Usado: Directo de SymPy")
            return str(inversa)
        except Exception as e:
            print(f" No se pudo con método directo: {e}")

        # Intentar resolver con Fracciones Parciales
        try:
            descomposicion = sp.apart(expresion, s)
            print(f" Método Usado: Fracciones Parciales")
            print(f" Expresión descompuesta: {descomposicion}")
            
            # Calcular la inversa de Laplace de cada término
            terminos = [sp.inverse_laplace_transform(term, s, t).expand(trig=True) for term in descomposicion.as_ordered_terms()]
            inversa = sum(terminos)
            inversa = sp.simplify(inversa)
            
            return str(inversa)
        except Exception as e:
            print(f" No se pudo hacer fracciones parciales: {e}")

        # 3️⃣ Si todo falla, usar Método Numérico
        print(f" Método Usado: Aproximación Numérica")
        inversa_numerica = sp.inverse_laplace_transform(expresion, s, t, noconds=True)
        inversa_numerica = sp.simplify(inversa_numerica.expand(trig=True))  # Convertir imaginarios a senos/cosenos
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
