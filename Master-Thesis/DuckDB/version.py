import duckdb

# Połączenie z bazą w pamięci (na potrzeby testów)
con = duckdb.connect()

# Wersja DuckDB – funkcja version()
duckdb_version = con.execute("SELECT version()").fetchone()[0]
print("DuckDB version:", duckdb_version)

# Szczegółowe informacje z PRAGMA version
pragma_version = con.execute("PRAGMA version").fetchone()
print("PRAGMA version:", pragma_version)

# Instalacja i załadowanie rozszerzenia spatial
con.install_extension("spatial")
con.load_extension("spatial")

# Weryfikacja, czy rozszerzenie spatial jest zainstalowane i załadowane
spatial_status = con.execute(
    """
    SELECT
        extension_name,
        installed,
        loaded,
        extension_version
    FROM duckdb_extensions()
    WHERE extension_name = 'spatial'
"""
).fetchone()
print("Spatial extension status:", spatial_status)

# Wersja biblioteki PROJ używanej przez DuckDB Spatial (jeśli dostępna)
proj_runtime = con.execute("SELECT duckdb_proj_version()").fetchone()[0]
proj_compiled = con.execute("SELECT duckdb_proj_compiled_version()").fetchone()[0]
print("PROJ runtime version:", proj_runtime)
print("PROJ compiled version:", proj_compiled)
