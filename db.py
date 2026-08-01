from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import os
from pathlib import Path
dotenv_path = find_dotenv(usecwd=True)
load_dotenv(find_dotenv(), override=True)
ROOT = Path(dotenv_path).resolve().parent if dotenv_path else Path.cwd()

## Load SQL
def resolve_path(p):
    """Resolusikan path relatif terhadap root repo (bukan cwd notebook)."""
    p = Path(p)
    return p if p.is_absolute() else (ROOT / p)

mysql_url = URL.create(
    "mysql+pymysql",
    username=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    host=os.getenv("MYSQL_HOST"),
    port=int(os.getenv("MYSQL_PORT")),
    database=os.getenv("MYSQL_DATABASE"),
)
ca_path = str(resolve_path(os.getenv("MYSQL_SSL_CA")))  # Aiven wajib SSL
engine = create_engine(mysql_url, connect_args={"ssl": {"ca": ca_path}})

# Uji koneksi cepat
with engine.connect() as c:
    print("MySQL  :", c.execute(text("SELECT VERSION()")).scalar())
