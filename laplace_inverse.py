from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import sympy as sp
from sympy import symbols, apart, simplify, fraction, inverse_laplace_transform
from mpmath import invertlaplace
import mpmath as mp
import numpy as np

# Ruta ligera para UptimeRobot
@app.route('/')
def home():
    return '🟢 API de Laplace activa'

@app.route('/ping')
def ping():
    return 'pong'

app = Flask(__name__)
CORS(app)

s, t = sp.symbols('s t')
mp.dps = 15

def filtrar_numeros_pequenos(expresion, umbral=1e-10):
    return expresion.xreplace({n: 0 for n in expresion.atoms(sp.Number) if abs(n) < umbral})

def aplicar_identidad_euler(expresion):
    expresion = expresion.expand()
    for termino in expresion.atoms(sp.exp):
        argumento = termino.args[0]
        if argumento.has(sp.I):
            a, b = sp.re(argumento), sp.im(argumento)
            nueva_exp = sp.exp(a*t) * (sp.cos(b*t) + sp.I * sp.sin(b*t))
            expresion = expresion.subs(termino, nueva_exp)
    return sp.simplify(expresion)

def simplificar_por_residuos(H_str, umbral=0.01):
    try:
        H = sp.sympify(H_str)
        Hs = H / s
        H_apart = apart(Hs, s, full=True)

        terminos = H_apart.as_ordered_terms()
        terminos_filtrados = []
        polos_descartados = []
        polos_aceptados = []

        for term in terminos:
            num, denom = fraction(term)
            if denom.is_polynomial(s) and num.is_number:
                residuo = abs(num.evalf())
                polos = denom.as_poly(s).all_roots()
                polo = polos[0] if polos else "desconocido"

                if residuo > umbral:
                    terminos_filtrados.append(term)
                    polos_aceptados.append((float(polo.evalf()), float(residuo)))
                else:
                    polos_descartados.append((float(polo.evalf()), float(residuo)))
            else:
                terminos_filtrados.append(term)

        H_simplificada = simplify(sum(terminos_filtrados))

        # Intentar métodos en orden
        try:
            h_t = inverse_laplace_transform(H_simplificada, s, t)
            h_t = aplicar_identidad_euler(h_t)
            h_t = filtrar_numeros_pequenos(h_t)
            return {
                "tipo": "simbolico",
                "resultado": str(h_t).replace("Heaviside(t)", "1"),
                "H_simplificada": str(H_simplificada),
                "poles_aceptados": polos_aceptados,
                "poles_descartados": polos_descartados
            }
        except Exception as e1:
            try:
                descomp = apart(H_simplificada, s)
                h_t = inverse_laplace_transform(descomp, s, t)
                h_t = aplicar_identidad_euler(h_t)
                h_t = filtrar_numeros_pequenos(h_t)
                return {
                    "tipo": "simbolico",
                    "resultado": str(h_t).replace("Heaviside(t)", "1"),
                    "H_simplificada": str(H_simplificada),
                    "poles_aceptados": polos_aceptados,
                    "poles_descartados": polos_descartados
                }
            except Exception as e2:
                def laplace_func(s_num):
                    try:
                        f = sp.lambdify(s, H_simplificada, modules=["mpmath", "numpy"])
                        return f(s_num)
                    except:
                        return 0

                try:
                    valores_t = np.linspace(0.01, 10, 100)
                    resultado_numerico = [float(invertlaplace(laplace_func, ti)) for ti in valores_t]
                    resultado_t = list(map(float, valores_t))
                    return {
                        "tipo": "numerico",
                        "puntos": list(zip(resultado_t, resultado_numerico)),
                        "H_simplificada": str(H_simplificada),
                        "poles_aceptados": polos_aceptados,
                        "poles_descartados": polos_descartados
                    }
                except Exception as final_e:
                    return {
                        "tipo": "error",
                        "mensaje": f"Error en método numérico (mpmath): {str(final_e)}"
                    }

    except Exception as e:
        return {
            "tipo": "error",
            "mensaje": f"Error general: {str(e)}"
        }

@app.route('/laplace', methods=['GET'])
@cross_origin(origin="*")
def calcular_laplace():
    expresion = request.args.get('expresion', "1 / (s + 1)")
    resultado = simplificar_por_residuos(expresion, umbral=0.01)

    if resultado.get("tipo") == "error":
        return jsonify({"tipo": "error", "mensaje": resultado.get("mensaje", "Error desconocido")})

    if resultado.get("tipo") == "simbolico":
        return jsonify({
            "tipo": "simbolico",
            "resultado": resultado["resultado"],
            "H_simplificada": resultado["H_simplificada"],
            "poles_aceptados": resultado["poles_aceptados"],
            "poles_descartados": resultado["poles_descartados"]
        })

    if resultado.get("tipo") == "numerico":
        return jsonify({
            "tipo": "numerico",
            "puntos": resultado["puntos"],
            "H_simplificada": resultado["H_simplificada"],
            "poles_aceptados": resultado["poles_aceptados"],
            "poles_descartados": resultado["poles_descartados"]
        })

    return jsonify({"tipo": "error", "mensaje": "Respuesta inesperada del servidor"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
