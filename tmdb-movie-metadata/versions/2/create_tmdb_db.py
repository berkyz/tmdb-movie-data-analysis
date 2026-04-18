# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import ast
import pyodbc
import warnings
warnings.filterwarnings('ignore')

DB_NAME  = 'TMDB_MovieDB'
SERVER   = r'.\SQLEXPRESS'
DRIVER   = 'ODBC Driver 17 for SQL Server'
CSV_FILE = 'tmdb_5000_merged.csv'

def get_conn(database='master'):
    return pyodbc.connect(
        'DRIVER={%s};SERVER=%s;DATABASE=%s;Trusted_Connection=yes;TrustServerCertificate=yes;'
        % (DRIVER, SERVER, database),
        autocommit=True
    )

def safe_parse(val):
    try:
        return ast.literal_eval(val) if pd.notna(val) else []
    except:
        return []

def sv(v, n):
    return str(v)[:n] if pd.notna(v) else None

def iv(v):
    return int(v) if pd.notna(v) else None

def fv(v):
    return float(v) if pd.notna(v) else None

def to_date(v):
    try:
        return pd.to_datetime(v).date() if pd.notna(v) else None
    except:
        return None

def batch_ins(conn, sql, rows, batch=2000):
    cur = conn.cursor()
    cur.fast_executemany = True
    for i in range(0, len(rows), batch):
        cur.executemany(sql, rows[i:i+batch])
    conn.commit()

# -----------------------------------------------------------------------
# 1) Veritabani olustur
# -----------------------------------------------------------------------
print('[1/9] Veritabani olusturuluyor: %s' % DB_NAME)
with get_conn('master') as conn:
    conn.cursor().execute(
        "IF DB_ID(N'%s') IS NULL CREATE DATABASE [%s]" % (DB_NAME, DB_NAME)
    )
print('      -> OK')

# -----------------------------------------------------------------------
# 2) Tablolar
# -----------------------------------------------------------------------
print('[2/9] Tablolar olusturuluyor...')

DDL = [
"""IF OBJECT_ID('dbo.Movies','U') IS NULL
CREATE TABLE dbo.Movies (
    movie_id            INT             NOT NULL,
    title               NVARCHAR(500),
    original_title      NVARCHAR(500),
    original_language   NVARCHAR(10),
    budget              BIGINT,
    revenue             BIGINT,
    popularity          FLOAT,
    runtime             FLOAT,
    release_date        DATE,
    status              NVARCHAR(50),
    tagline             NVARCHAR(1000),
    overview            NVARCHAR(MAX),
    vote_average        FLOAT,
    vote_count          INT,
    homepage            NVARCHAR(1000),
    CONSTRAINT PK_Movies PRIMARY KEY (movie_id)
)""",
"""IF OBJECT_ID('dbo.Genres','U') IS NULL
CREATE TABLE dbo.Genres (
    genre_id    INT           NOT NULL,
    genre_name  NVARCHAR(100) NOT NULL,
    CONSTRAINT PK_Genres PRIMARY KEY (genre_id)
)""",
"""IF OBJECT_ID('dbo.Movie_Genres','U') IS NULL
CREATE TABLE dbo.Movie_Genres (
    movie_id  INT NOT NULL,
    genre_id  INT NOT NULL,
    CONSTRAINT PK_Movie_Genres    PRIMARY KEY (movie_id, genre_id),
    CONSTRAINT FK_MG_Movie        FOREIGN KEY (movie_id) REFERENCES dbo.Movies(movie_id),
    CONSTRAINT FK_MG_Genre        FOREIGN KEY (genre_id) REFERENCES dbo.Genres(genre_id)
)""",
"""IF OBJECT_ID('dbo.Keywords','U') IS NULL
CREATE TABLE dbo.Keywords (
    keyword_id    INT           NOT NULL,
    keyword_name  NVARCHAR(300) NOT NULL,
    CONSTRAINT PK_Keywords PRIMARY KEY (keyword_id)
)""",
"""IF OBJECT_ID('dbo.Movie_Keywords','U') IS NULL
CREATE TABLE dbo.Movie_Keywords (
    movie_id    INT NOT NULL,
    keyword_id  INT NOT NULL,
    CONSTRAINT PK_Movie_Keywords   PRIMARY KEY (movie_id, keyword_id),
    CONSTRAINT FK_MK_Movie         FOREIGN KEY (movie_id)   REFERENCES dbo.Movies(movie_id),
    CONSTRAINT FK_MK_Keyword       FOREIGN KEY (keyword_id) REFERENCES dbo.Keywords(keyword_id)
)""",
"""IF OBJECT_ID('dbo.Production_Companies','U') IS NULL
CREATE TABLE dbo.Production_Companies (
    company_id    INT           NOT NULL,
    company_name  NVARCHAR(500) NOT NULL,
    CONSTRAINT PK_Companies PRIMARY KEY (company_id)
)""",
"""IF OBJECT_ID('dbo.Movie_Production_Companies','U') IS NULL
CREATE TABLE dbo.Movie_Production_Companies (
    movie_id    INT NOT NULL,
    company_id  INT NOT NULL,
    CONSTRAINT PK_Movie_Companies  PRIMARY KEY (movie_id, company_id),
    CONSTRAINT FK_MPC_Movie        FOREIGN KEY (movie_id)   REFERENCES dbo.Movies(movie_id),
    CONSTRAINT FK_MPC_Company      FOREIGN KEY (company_id) REFERENCES dbo.Production_Companies(company_id)
)""",
"""IF OBJECT_ID('dbo.Production_Countries','U') IS NULL
CREATE TABLE dbo.Production_Countries (
    iso_3166_1    NCHAR(2)      NOT NULL,
    country_name  NVARCHAR(200) NOT NULL,
    CONSTRAINT PK_Countries PRIMARY KEY (iso_3166_1)
)""",
"""IF OBJECT_ID('dbo.Movie_Production_Countries','U') IS NULL
CREATE TABLE dbo.Movie_Production_Countries (
    movie_id    INT      NOT NULL,
    iso_3166_1  NCHAR(2) NOT NULL,
    CONSTRAINT PK_Movie_Countries  PRIMARY KEY (movie_id, iso_3166_1),
    CONSTRAINT FK_MPCO_Movie       FOREIGN KEY (movie_id)   REFERENCES dbo.Movies(movie_id),
    CONSTRAINT FK_MPCO_Country     FOREIGN KEY (iso_3166_1) REFERENCES dbo.Production_Countries(iso_3166_1)
)""",
"""IF OBJECT_ID('dbo.Spoken_Languages','U') IS NULL
CREATE TABLE dbo.Spoken_Languages (
    iso_639_1      NCHAR(2)      NOT NULL,
    language_name  NVARCHAR(100) NOT NULL,
    CONSTRAINT PK_Languages PRIMARY KEY (iso_639_1)
)""",
"""IF OBJECT_ID('dbo.Movie_Spoken_Languages','U') IS NULL
CREATE TABLE dbo.Movie_Spoken_Languages (
    movie_id   INT      NOT NULL,
    iso_639_1  NCHAR(2) NOT NULL,
    CONSTRAINT PK_Movie_Languages  PRIMARY KEY (movie_id, iso_639_1),
    CONSTRAINT FK_MSL_Movie        FOREIGN KEY (movie_id)  REFERENCES dbo.Movies(movie_id),
    CONSTRAINT FK_MSL_Language     FOREIGN KEY (iso_639_1) REFERENCES dbo.Spoken_Languages(iso_639_1)
)""",
"""IF OBJECT_ID('dbo.Persons','U') IS NULL
CREATE TABLE dbo.Persons (
    person_id  INT           NOT NULL,
    name       NVARCHAR(300) NOT NULL,
    gender     TINYINT,
    CONSTRAINT PK_Persons PRIMARY KEY (person_id)
)""",
"""IF OBJECT_ID('dbo.Cast','U') IS NULL
CREATE TABLE dbo.Cast (
    credit_id   NVARCHAR(50)  NOT NULL,
    movie_id    INT           NOT NULL,
    person_id   INT           NOT NULL,
    cast_id     INT,
    character   NVARCHAR(500),
    cast_order  INT,
    CONSTRAINT PK_Cast          PRIMARY KEY (credit_id),
    CONSTRAINT FK_Cast_Movie    FOREIGN KEY (movie_id)  REFERENCES dbo.Movies(movie_id),
    CONSTRAINT FK_Cast_Person   FOREIGN KEY (person_id) REFERENCES dbo.Persons(person_id)
)""",
"""IF OBJECT_ID('dbo.Crew','U') IS NULL
CREATE TABLE dbo.Crew (
    credit_id   NVARCHAR(50)  NOT NULL,
    movie_id    INT           NOT NULL,
    person_id   INT           NOT NULL,
    department  NVARCHAR(100),
    job         NVARCHAR(200),
    CONSTRAINT PK_Crew          PRIMARY KEY (credit_id),
    CONSTRAINT FK_Crew_Movie    FOREIGN KEY (movie_id)  REFERENCES dbo.Movies(movie_id),
    CONSTRAINT FK_Crew_Person   FOREIGN KEY (person_id) REFERENCES dbo.Persons(person_id)
)"""
]

with get_conn(DB_NAME) as conn:
    cur = conn.cursor()
    for stmt in DDL:
        cur.execute(stmt)
print('      -> 14 tablo OK')

# -----------------------------------------------------------------------
# 3) CSV oku
# -----------------------------------------------------------------------
print('[3/9] CSV okunuyor...')
df = pd.read_csv(CSV_FILE)
print('      -> %d film yuklendi' % len(df))

# -----------------------------------------------------------------------
# 4) Movies
# -----------------------------------------------------------------------
print('[4/9] Movies tablosu dolduruluyor...')
rows = []
for _, r in df.iterrows():
    rows.append((
        iv(r['id']),
        sv(r.get('title'), 500),
        sv(r.get('original_title'), 500),
        sv(r.get('original_language'), 10),
        iv(r.get('budget')),
        iv(r.get('revenue')),
        fv(r.get('popularity')),
        fv(r.get('runtime')),
        to_date(r.get('release_date')),
        sv(r.get('status'), 50),
        sv(r.get('tagline'), 1000),
        sv(r.get('overview'), 4000),
        fv(r.get('vote_average')),
        iv(r.get('vote_count')),
        sv(r.get('homepage'), 1000),
    ))
with get_conn(DB_NAME) as conn:
    conn.autocommit = False
    batch_ins(conn,
        'INSERT INTO dbo.Movies VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        rows)
print('      -> %d kayit OK' % len(rows))

# -----------------------------------------------------------------------
# 5) Genres
# -----------------------------------------------------------------------
print('[5/9] Genres...')
gd = {}
mg = []
for _, r in df.iterrows():
    for g in safe_parse(r['genres']):
        gd[g['id']] = g['name']
        mg.append((iv(r['id']), g['id']))
mg = list(set(mg))
with get_conn(DB_NAME) as conn:
    conn.autocommit = False
    batch_ins(conn, 'INSERT INTO dbo.Genres VALUES (?,?)',
              [(k, v[:100]) for k, v in gd.items()])
    batch_ins(conn, 'INSERT INTO dbo.Movie_Genres VALUES (?,?)', mg)
print('      -> %d tur, %d iliski OK' % (len(gd), len(mg)))

# -----------------------------------------------------------------------
# 6) Keywords
# -----------------------------------------------------------------------
print('[6/9] Keywords...')
kd = {}
mk = []
for _, r in df.iterrows():
    for k in safe_parse(r['keywords']):
        kd[k['id']] = k['name']
        mk.append((iv(r['id']), k['id']))
mk = list(set(mk))
with get_conn(DB_NAME) as conn:
    conn.autocommit = False
    batch_ins(conn, 'INSERT INTO dbo.Keywords VALUES (?,?)',
              [(k, v[:300]) for k, v in kd.items()])
    batch_ins(conn, 'INSERT INTO dbo.Movie_Keywords VALUES (?,?)', mk)
print('      -> %d keyword, %d iliski OK' % (len(kd), len(mk)))

# -----------------------------------------------------------------------
# 7) Production Companies
# -----------------------------------------------------------------------
print('[7/9] Production Companies...')
cd = {}
mc = []
for _, r in df.iterrows():
    for c in safe_parse(r['production_companies']):
        cd[c['id']] = c['name']
        mc.append((iv(r['id']), c['id']))
mc = list(set(mc))
with get_conn(DB_NAME) as conn:
    conn.autocommit = False
    batch_ins(conn, 'INSERT INTO dbo.Production_Companies VALUES (?,?)',
              [(k, v[:500]) for k, v in cd.items()])
    batch_ins(conn, 'INSERT INTO dbo.Movie_Production_Companies VALUES (?,?)', mc)
print('      -> %d sirket, %d iliski OK' % (len(cd), len(mc)))

# -----------------------------------------------------------------------
# 8) Countries + Languages
# -----------------------------------------------------------------------
print('[8/9] Countries & Languages...')
cod = {}
mco = []
ld = {}
mla = []
for _, r in df.iterrows():
    for c in safe_parse(r['production_countries']):
        cod[c['iso_3166_1']] = c['name']
        mco.append((iv(r['id']), c['iso_3166_1']))
    for l in safe_parse(r['spoken_languages']):
        ld[l['iso_639_1']] = l['name']
        mla.append((iv(r['id']), l['iso_639_1']))
mco = list(set(mco))
mla = list(set(mla))
with get_conn(DB_NAME) as conn:
    conn.autocommit = False
    batch_ins(conn, 'INSERT INTO dbo.Production_Countries VALUES (?,?)',
              [(k, v[:200]) for k, v in cod.items()])
    batch_ins(conn, 'INSERT INTO dbo.Movie_Production_Countries VALUES (?,?)', mco)
    batch_ins(conn, 'INSERT INTO dbo.Spoken_Languages VALUES (?,?)',
              [(k, v[:100]) for k, v in ld.items()])
    batch_ins(conn, 'INSERT INTO dbo.Movie_Spoken_Languages VALUES (?,?)', mla)
print('      -> %d ulke, %d dil OK' % (len(cod), len(ld)))

# -----------------------------------------------------------------------
# 9) Persons + Cast + Crew
# -----------------------------------------------------------------------
print('[9/9] Persons / Cast / Crew...')
persons = {}
cast_rows = []
crew_rows = []
seen_c  = set()
seen_cr = set()

for _, r in df.iterrows():
    mid = iv(r['id'])
    for c in safe_parse(r['cast']):
        pid = c.get('id')
        if pid is None:
            continue
        persons[pid] = (str(c.get('name', ''))[:300], c.get('gender'))
        cid = c.get('credit_id', '')
        if cid and cid not in seen_c:
            seen_c.add(cid)
            cast_rows.append((
                str(cid)[:50], mid, int(pid),
                c.get('cast_id'),
                str(c.get('character', ''))[:500] if c.get('character') else None,
                c.get('order'),
            ))
    for c in safe_parse(r['crew']):
        pid = c.get('id')
        if pid is None:
            continue
        persons[pid] = (str(c.get('name', ''))[:300], c.get('gender'))
        cid = c.get('credit_id', '')
        if cid and cid not in seen_cr:
            seen_cr.add(cid)
            crew_rows.append((
                str(cid)[:50], mid, int(pid),
                str(c.get('department', ''))[:100] if c.get('department') else None,
                str(c.get('job', ''))[:200]        if c.get('job')        else None,
            ))

person_rows = [(pid, name, gender) for pid, (name, gender) in persons.items()]

with get_conn(DB_NAME) as conn:
    conn.autocommit = False
    batch_ins(conn, 'INSERT INTO dbo.Persons VALUES (?,?,?)', person_rows)
    print('      -> %d kisi OK' % len(person_rows))

with get_conn(DB_NAME) as conn:
    conn.autocommit = False
    batch_ins(conn, 'INSERT INTO dbo.Cast VALUES (?,?,?,?,?,?)', cast_rows)
    print('      -> %d cast kaydi OK' % len(cast_rows))

with get_conn(DB_NAME) as conn:
    conn.autocommit = False
    batch_ins(conn, 'INSERT INTO dbo.Crew VALUES (?,?,?,?,?)', crew_rows)
    print('      -> %d crew kaydi OK' % len(crew_rows))

# -----------------------------------------------------------------------
# Ozet
# -----------------------------------------------------------------------
print()
print('='*58)
print('  TAMAMLANDI  |  DB: %s  |  Sunucu: %s' % (DB_NAME, SERVER))
print('='*58)
TABLES = [
    'Movies', 'Genres', 'Movie_Genres', 'Keywords', 'Movie_Keywords',
    'Production_Companies', 'Movie_Production_Companies',
    'Production_Countries', 'Movie_Production_Countries',
    'Spoken_Languages', 'Movie_Spoken_Languages',
    'Persons', 'Cast', 'Crew'
]
with get_conn(DB_NAME) as conn:
    cur = conn.cursor()
    for t in TABLES:
        cur.execute('SELECT COUNT(*) FROM dbo.[%s]' % t)
        cnt = cur.fetchone()[0]
        print('  dbo.%-38s %8d satir' % (t, cnt))
print('='*58)
