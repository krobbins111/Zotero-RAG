from pyzotero import zotero
import os
import requests
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.vectorstores.qdrant import Qdrant


import config


def download_pdf(pdf_url, save_path):
    try:
        if 'arxiv' in pdf_url:
            pdf_url = pdf_url.replace('/abs/', '/pdf/')
        response = requests.get(pdf_url)
        if response.status_code == 200 and response.headers['Content-Type'] == 'application/pdf':
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        elif response.status_code != 200:
            print(f'Http request failed with code: {response.status_code}')
        elif response.headers['Content-Type'] != 'application/pdf':
            print('Received non-PDF data from download request')
            print(response.headers['Content-Type'])
        else:
            print(response.headers['Content-Type'])
    except Exception as e:
        print(f'Failed to download PDF from {pdf_url} due to: {e}')
    return False

def test_connection(user_id, api_key):
    zot = zotero.Zotero(user_id, 'user', api_key)
    try:
        items_test = zot.top(limit=1)
        if items_test:
            return 'Connection Successful'
    except Exception:
        return 'Failed to connect to Zotero. Check credentials.'
    return 'Connection Successful but your library is empty.'


def embed_all_pdfs(tags_query, user_id, api_key):
    # Replace with your Zotero credentials
    ZOTERO_LIBRARY_TYPE = 'user'
    print(user_id, ZOTERO_LIBRARY_TYPE, api_key)
    zot = zotero.Zotero(user_id, ZOTERO_LIBRARY_TYPE, api_key)

    # Get all items with the specific tags
    all_items = {}
    tags = tags_query.replace(' ,', ',').replace(', ', ',').split(',')
    for tag in tags:
        items = zot.everything(zot.items(tag=tag))
        for item in items:
            all_items[item['key']] = item
    analyze_count = 0
    zotero_data_map = {}

    for item_key, item in all_items.items():
        if 'url' in item['data']:
                pdf_name = f"{item['key']}.pdf"
                save_path = os.path.join(os.getcwd(), config.DOWNLOAD_DIR, pdf_name)

                # Download the PDF
                if download_pdf(item['data']['url'], save_path):
                    print(f"Downloaded: {pdf_name}")
                    analyze_count += 1
                    zotero_data_map.update({item['key']: item})
                    # Clean up
                    # os.remove(save_path)
                else:
                    print(f"Failed to download PDF for: {item['data']['url']}")
            
    dir_path = os.path.join(os.getcwd(), config.DOWNLOAD_DIR)
    loader = DirectoryLoader(
        dir_path,
        glob='**/*.pdf',
        loader_cls=PyPDFLoader,
        show_progress=True
    )
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3072,
        chunk_overlap=64
    )
    texts = text_splitter.split_documents(documents)
    prepared_documents = []
    print(texts[0].metadata)
    for text in texts:
        doc_name = os.path.basename(text.metadata['source'])
        doc_name = os.path.splitext(doc_name)[0]
        print(doc_name)
        new_text = text
        new_text.metadata = zotero_data_map.get(doc_name)
        print(new_text)
        prepared_documents.append(new_text)

    Qdrant.from_documents(
        prepared_documents,
        config.EMBEDDING_FUNCTION,
        collection_name=config.COLLECTION_NAME,
        url=config.QDRANT_URL
    )
    return f'Analyzed {analyze_count} documents. You can now chat with your lit review.'