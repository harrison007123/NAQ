import threading
import logging
from flask import Flask, render_template, request, jsonify
import webbrowser

from naq import ai_engine, safety, executor
from rich.console import Console

app = Flask(__name__)
console = Console()

_APP_STATE = {
    "cfg": None,
    "conn": None,
    "schema_text": ""
}

@app.route("/")
def index():
    return render_template("index.html", db_type=_APP_STATE["cfg"].get("db_type", "Database"))

@app.route("/api/schema", methods=["GET"])
def get_schema():
    return jsonify({"schema": _APP_STATE["schema_text"]})

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.json
    question = data.get("question", "")
    
    try:
        # Generate SQL
        queries = ai_engine.generate_sql(_APP_STATE["cfg"], _APP_STATE["schema_text"], question)
        
        # Validate Safety
        warnings = []
        requires_confirmation = False
        
        for q in queries:
            is_safe, msg = safety.check_sql(q)
            if not is_safe:
                requires_confirmation = True
                warnings.append(msg)
                
        return jsonify({
            "queries": queries,
            "requires_confirmation": requires_confirmation,
            "warnings": warnings,
            "error": None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/execute", methods=["POST"])
def execute():
    data = request.json
    queries = data.get("queries", [])
    
    if not queries:
        return jsonify({"error": "No queries provided."}), 400
        
    try:
        result = executor.execute_query(_APP_STATE["conn"], queries)
        
        columns = list(result.df.columns)
        # Convert df to rows, replacing NaNs
        rows = result.df.fillna("").values.tolist()
        
        return jsonify({
            "columns": columns,
            "rows": rows,
            "row_count": result.row_count,
            "sql": result.sql,
            "error": None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/show_all", methods=["GET"])
def show_all():
    from naq import schema_loader
    try:
        schema = schema_loader.fetch_schema(_APP_STATE["conn"], _APP_STATE["cfg"])
        
        tables_data = {}
        for table_name in schema.keys():
            try:
                # Query the table
                query = f"SELECT * FROM {table_name}"
                result = executor.execute_query(_APP_STATE["conn"], [query])
                
                columns = list(result.df.columns)
                rows = result.df.fillna("").values.tolist()
                
                tables_data[table_name] = {
                    "columns": columns,
                    "rows": rows
                }
            except Exception as e:
                tables_data[table_name] = {"error": str(e)}
                
        return jsonify({"tables": tables_data, "error": None})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

def start_server(cfg, conn, schema_text):
    if _APP_STATE["cfg"] is not None:
        console.print("\n  [bold yellow]⚠[/bold yellow] Web server is already running across http://127.0.0.1:5000")
        webbrowser.open("http://127.0.0.1:5000")
        return

    _APP_STATE["cfg"] = cfg
    _APP_STATE["conn"] = conn
    _APP_STATE["schema_text"] = schema_text

    # Disable flask logging spam
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    console.print("\n  [bold green]✓[/bold green] Launching NAQ Web Interface on http://127.0.0.1:5000")
    
    def run():
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

    server_thread = threading.Thread(target=run, daemon=True)
    server_thread.start()
    
    webbrowser.open("http://127.0.0.1:5000")
