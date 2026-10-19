from app import BOOKS, app, DB_NAME, init_db
import os
import sqlite3


def setup_database():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    init_db()

def teardown_database():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)


def test_main_pages():
    setup_database()
    client = app.test_client()

    home = client.get('/')
    about = client.get('/about')
    library = client.get('/library')

    assert home.status_code == 200
    assert about.status_code == 200
    assert library.status_code == 200
    teardown_database()


def test_library_crud_flow():
    setup_database()
    client = app.test_client()
    title = 'Майстер і Маргарита'

    add_response = client.post('/library/add', data={
        'title': title,
        'author': 'Михайло Булгаков',
        'year': '1940',
        'borrower': 'Олена',
    }, follow_redirects=True)

    assert add_response.status_code == 200
    assert title.encode('utf-8') in add_response.data

    book = next((item for item in BOOKS if item['title'] == title), None)
    assert book is not None

    edit_response = client.post(f'/library/{book["id"]}/edit', data={
        'title': title,
        'author': 'Михайло Булгаков',
        'year': '1941',
        'borrower': 'Іван',
    }, follow_redirects=True)

    assert edit_response.status_code == 200
    assert 'Іван'.encode('utf-8') in edit_response.data

    delete_response = client.post(f'/library/{book["id"]}/delete', follow_redirects=True)
    assert delete_response.status_code == 200
    assert 'utf-8' not in delete_response.data
    teardown_database()  
