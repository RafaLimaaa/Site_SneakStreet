import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import pooling

# ====== Paths base e .env ======
BASE_DIR = Path(__file__).parent.resolve()
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

# ====== Config do banco (via .env) ======
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_NAME = os.getenv("DB_NAME", "loja_tenis")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 5))

# ====== Criação do app Flask com pastas corretas ======
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
app.secret_key = os.getenv("FLASK_SECRET", "troque_esta_chave")

# ====== Pool de conexões MySQL ======
# Obs: se der erro de acesso, confira user/senha no .env
cnxpool = pooling.MySQLConnectionPool(
    pool_name="loja_pool",
    pool_size=POOL_SIZE,
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME,
    autocommit=False,
)

def get_connection():
    """Pega uma conexão do pool."""
    return cnxpool.get_connection()

# ====== Rotas ======
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/produtos")
def produtos():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nome, preco, estoque FROM produtos ORDER BY id DESC;")
        rows = cur.fetchall()
        return render_template("produtos.html", produtos=rows)
    except mysql.connector.Error as e:
        return f"Erro ao listar produtos: {e}", 500
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass

@app.route("/api/products")
def api_products():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nome, preco, estoque FROM produtos ORDER BY id DESC;")
        rows = cur.fetchall()
        return jsonify(rows)
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass

@app.route("/adicionar", methods=["GET", "POST"])
def adicionar():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        preco = (request.form.get("preco") or "0").strip()
        estoque = (request.form.get("estoque") or "0").strip()

        # validação simples
        if not nome:
            return "Nome é obrigatório", 400
        try:
            preco_val = float(preco)
            estoque_val = int(estoque)
        except ValueError:
            return "Preço/Estoque inválidos", 400

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO produtos (nome, preco, estoque) VALUES (%s, %s, %s)",
                (nome, preco_val, estoque_val),
            )
            conn.commit()
            return redirect(url_for("produtos"))
        except mysql.connector.Error as e:
            try:
                conn.rollback()
            except Exception:
                pass
            return f"Erro ao inserir produto: {e}", 500
        finally:
            try:
                cur.close()
                conn.close()
            except Exception:
                pass

    # GET
    return render_template("adicionar.html")

@app.route("/deletar/<int:produto_id>", methods=["POST"])
def deletar(produto_id: int):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM produtos WHERE id = %s", (produto_id,))
        conn.commit()
        return redirect(url_for("produtos"))
    except mysql.connector.Error as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return f"Erro ao apagar produto: {e}", 500
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass

# ====== Handlers simples ======
@app.errorhandler(404)
def not_found(_e):
    return "Página não encontrada", 404

@app.errorhandler(500)
def internal(_e):
    return "Erro interno do servidor", 500

# ====== Bootstrap ======
if __name__ == "__main__":
    # Dica: no VS Code, execute no terminal com (venv) ativo:
    # python app.py
    app.run(host="127.0.0.1", port=5000, debug=True)
