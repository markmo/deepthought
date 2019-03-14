import atexit
from drqa import retriever
from flask import Flask, g, jsonify, request
import gensim
import numpy as np
import pandas as pd
from pathlib import Path
import pickle
from settings import DATABASE_NAME, MODEL_NAME
from sklearn.feature_extraction.text import CountVectorizer
import spacy
import sqlite3

ROOT_DIR = Path(__file__).parent
DATABASE = str(ROOT_DIR / 'database' / DATABASE_NAME)
MODEL = str(ROOT_DIR / 'model' / MODEL_NAME)

app = Flask(__name__)
# app.config.update(
#     CELERY_BROKER_URL='redis://localhost:6379',
#     CELERY_RESULT_BACKEND='redis://localhost:6379'
# )
# celery = make_celery(app)
ranker = None
nlp = None
df_topic_keywords = None
lda_model = None
vectorizer = None


def sent_to_words(sentences):
    for sentence in sentences:
        yield(gensim.utils.simple_preprocess(str(sentence), deacc=True))  # deacc=True removes punctuations


def lemmatization(texts, allowed_pos_tags=None):
    """https://spacy.io/api/annotation"""
    global nlp
    if allowed_pos_tags is None:
        allowed_pos_tags = ['NOUN', 'ADJ', 'VERB', 'ADV']

    texts_out = []
    for sent in texts:
        doc = nlp(" ".join(sent))
        texts_out.append(" ".join([token.lemma_ if token.lemma_ not in ['-PRON-'] else ''
                                   for token in doc if token.pos_ in allowed_pos_tags]))
    return texts_out


def predict_topic(text):
    global df_topic_keywords, lda_model, vectorizer

    # Step 1: Clean with simple_preprocess
    mytext_2 = list(sent_to_words(text))

    # Step 2: Lemmatize
    mytext_3 = lemmatization(mytext_2, allowed_pos_tags=['NOUN', 'ADJ', 'VERB', 'ADV'])

    # Step 3: Vectorize transform
    mytext_4 = vectorizer.transform(mytext_3)

    # Step 4: LDA Transform
    topic_probability_scores = lda_model.transform(mytext_4)
    topic = df_topic_keywords.iloc[np.argmax(topic_probability_scores), :].values.tolist()
    return topic, topic_probability_scores


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

    return db


# noinspection PyUnusedLocal
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
    global ranker, nlp, df_topic_keywords, lda_model, vectorizer
    print('Initializing app')
    ranker = retriever.get_class('tfidf')(tfidf_path=MODEL)
    print('ranker:', ranker)
    df_topic_keywords = pd.read_pickle(ROOT_DIR / 'model' / 'df_topic_keywords.pkl')
    lda_model = pickle.load(open(ROOT_DIR / 'model' / 'best_lda_model.pkl', 'rb'))
    vocabulary = pickle.load(open(ROOT_DIR / 'model' / 'tm_features.pkl', 'rb'))
    vectorizer = CountVectorizer(decode_error='replace', vocabulary=vocabulary)
    nlp = spacy.load('en', disable=['parser', 'ner'])


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


@app.route('/ask4')
def ask4():
    global ranker
    query = request.args['query']
    doc_ids, doc_scores = ranker.closest_docs(query, k=4)
    print('doc_ids', doc_ids)
    answers = []
    for i, doc_id in enumerate(doc_ids):
        ans = query_db('select text from documents where id=?', [doc_id], one=True)[0]
        answers.append((doc_scores[i], ans))

    return jsonify(answers)


@app.route('/topics')
def get_topics():
    query = request.args['query']
    topics, _ = predict_topic(query)
    topics.reverse()
    print(topics)
    return jsonify(topics[:3])


init()
atexit.register(shutdown)


if __name__ == '__main__':
    app.run()
