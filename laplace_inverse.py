from flask import Flask, request, jsonify 
from flask_cors import CORS, cross_origin
import sympy as sp
from sympy import symbols, simplify, fraction, inverse_laplace_transform
from mpmath import invertlaplace
import mpmath as mp
import numpy as np
from scipy import signal
import concurrent.futures
import multiprocessing

app = Flask(__name__)
CORS(app)

# Ruta ligera para UptimeRobot
@app.route('/')
def home():
    return '🟢 API de Laplace activa'

@app.route('/ping')
def ping():
    return 'pong'

s, t = sp.symbols('s t')
mp.dps = 15

def orden_transferencia(expr):
    try:
        num, den = fraction(expr)
        return sp.degree(den)  # Solo nos interesa el orden del denominador (orden del sistema)
    except:
        return 10  # Si no se puede obtener, asumimos un orden alto

def intentar_simbolico(expr, timeout=5):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(inverse_laplace_transform, expr, s, t)
        try:
            return future.result(timeout=timeout), "inverse_laplace_transform"
        except concurrent.futures.TimeoutError:
            raise TimeoutError("inverse_laplace_transform timed out")

def intentar_apart(expr, timeout=5):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(sp.apart, expr, s)
        try:
            return future.result(timeout=timeout), "apart"
        except concurrent.futures.TimeoutError:
            raise TimeoutError("apart() timed out")

@app.route('/laplace', methods=['GET'])
@cross_origin(origin="*")
def calcular_laplace():
    expresion = request.args.get('expresion', "1 / (s + 1)")

    try:
        H = sp.sympify(expresion)
        Hs = H / s  # ya estamos agregando el escalón aquí

        # Intentar siempre el método simbólico (aunque sea de orden alto)
        try:
            h_t, metodo1 = intentar_simbolico(Hs)
            return jsonify({
                "tipo": "simbolico",
                "metodo": metodo1,
                "resultado": str(h_t).replace("Heaviside(t)", "1"),
                "H_simplificada": str(Hs)
            })
        except Exception as e1:
            try:
                descomp, metodo2 = intentar_apart(Hs)
                h_t, metodo3 = intentar_simbolico(descomp)
                return jsonify({
                    "tipo": "simbolico",
                    "metodo": metodo3 + " (tras " + metodo2 + ")",
                    "resultado": str(h_t).replace("Heaviside(t)", "1"),
                    "H_simplificada": str(Hs)
                })
            except Exception as e2:
                pass  # continuar con métodos numéricos

        # Si fallo simbólico → método numérico (scipy)
        try:
            num, den = fraction(Hs)
            num_poly = sp.Poly(num, s)
            den_poly = sp.Poly(den, s)
            num_coeffs = [float(c) for c in num_poly.all_coeffs()]
            den_coeffs = [float(c) for c in den_poly.all_coeffs()]

            system = signal.TransferFunction(num_coeffs, den_coeffs)
            t_vals, y_vals = signal.step(system)

            return jsonify({
                "tipo": "numerico",
                "metodo": "scipy.step",
                "puntos": list(zip(t_vals.tolist(), y_vals.tolist())),
                "H_simplificada": str(Hs)
            })
        except Exception as e3:
            try:
                def laplace_func(s_num):
                    try:
                        f = sp.lambdify(s, Hs, modules=["mpmath", "numpy"])
                        return f(s_num)
                    except:
                        return 0

                valores_t = np.linspace(0.01, 10, 100)
                resultado_numerico = [float(invertlaplace(laplace_func, ti)) for ti in valores_t]
                resultado_t = list(map(float, valores_t))

                return jsonify({
                    "tipo": "numerico",
                    "metodo": "mpmath.invertlaplace",
                    "puntos": list(zip(resultado_t, resultado_numerico)),
                    "H_simplificada": str(Hs)
                })
            except Exception as final_e:
                return jsonify({
                    "tipo": "error",
                    "mensaje": f"Error en método numérico (mpmath): {str(final_e)}"
                })

    except Exception as e:
        return jsonify({
            "tipo": "error",
            "mensaje": f"Error general: {str(e)}"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
