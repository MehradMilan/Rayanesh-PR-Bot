import sqlite3


def init_db():
    conn = sqlite3.connect("documents.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_files (
            user_id INTEGER,
            folder_id TEXT,
            document_id TEXT,
            doc_code TEXT,
            PRIMARY KEY (user_id, folder_id)
        )
    """
    )
    conn.commit()
    conn.close()


def has_user_created_in_folder(user_id, folder_id):
    conn = sqlite3.connect("documents.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT document_id FROM user_files WHERE user_id = ? AND folder_id = ?",
        (user_id, folder_id),
    )
    result = cursor.fetchone()
    conn.close()
    return result


def update_user_document(user_id, folder_id, document_id, doc_code):
    conn = sqlite3.connect("documents.db")
    cursor = conn.cursor()
    cursor.execute(
        "REPLACE INTO user_files (user_id, folder_id, document_id, doc_code) VALUES (?, ?, ?, ?)",
        (user_id, folder_id, document_id, doc_code),
    )
    conn.commit()
    conn.close()


def get_document_id_by_doc_code(doc_code):
    conn = sqlite3.connect("documents.db")
    cursor = conn.cursor()
    cursor.execute("SELECT document_id FROM user_files WHERE doc_code = ?", (doc_code,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def delete_doc_by_code(doc_code):
    conn = sqlite3.connect("documents.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_files WHERE doc_code = ?", (doc_code,))
    conn.commit()
    conn.close()
