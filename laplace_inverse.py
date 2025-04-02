from flask import Flask, request, jsonify
import sympy as sp

app = Flask(__name__)

s, t = sp.symbols('s t')

def inversa_laplace(expresion_str):
    try:
        expresion = sp.sympify(expresion_str)
        inversa = sp.inverse_laplace_transform(expresion, s, t)
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
