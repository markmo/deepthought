import atexit
from drqa import retriever
from flask import Flask, g, request
from pathlib import Path
import sqlite3

ROOT_DIR = Path(__file__).parent
DATABASE = str(ROOT_DIR / 'database' / 'legal.db')
MODEL = str(ROOT_DIR / 'model' / 'legal-tfidf-ngram=2-hash=16777216-tokenizer=simple.npz')

app = Flask(__name__)
# app.config.update(
#     CELERY_BROKER_URL='redis://localhost:6379',
#     CELERY_RESULT_BACKEND='redis://localhost:6379'
# )
# celery = make_celery(app)
ranker = None


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, query_args=(), one=False):
    cur = get_db().execute(query, query_args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def init():
    global ranker
    print('Initializing app')
    ranker = retriever.get_class('tfidf')(tfidf_path=MODEL)
    print('ranker:', ranker)


def shutdown():
    pass


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/ask')
def ask():
    global ranker
    query = request.args['query']
    doc_ids, doc_scores = ranker.closest_docs(query, k=1)
    print('doc_ids', doc_ids)
    ans = query_db('select text from documents where id=?', [doc_ids[0]], one=True)[0]
    print(query, ans)
    return ans


init()
atexit.register(shutdown)


if __name__ == '__main__':
    app.run()
