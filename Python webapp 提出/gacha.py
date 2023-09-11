from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
DATABASE = 'gacha.db'
MEMO_DATABASE = 'gacha_memo.db'
app.secret_key = 'some_secret_key'  

class DatabaseConnection: #データベース接続を抽象化するクラス
    def __init__(self, db_name=DATABASE):
        self.db_name = db_name
        self.connection = None

    def __enter__(self):
        self.connection = sqlite3.connect(self.db_name)
        return self.connection.cursor()

    def __exit__(self, exc_type, exc_value, traceback):

        self.connection.commit()
        self.connection.close()

def fetch_histories(): #履歴を所得する関数
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT * FROM history ORDER BY id DESC")
        return cursor.fetchall()

def save_history(input_probability, times, calculated_probability): #履歴を保存する関数
    with DatabaseConnection() as cursor:
        cursor.execute("INSERT INTO history (input_probability, times, calculated_probability) VALUES (?, ?, ?)", 
                       (input_probability, times, calculated_probability))

def entry_exists(entry_id): #指定したIDのエントリが存在するかチェックする関数
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT * FROM history WHERE id=?", (entry_id,))
        return bool(cursor.fetchone())

def fetch_memo_content():  #メモの内容を取得する関数
    with DatabaseConnection(MEMO_DATABASE) as cursor:
        cursor.execute("SELECT content FROM memo")
        memo_content = cursor.fetchone()
        return memo_content[0] if memo_content else None

def save_or_update_memo(content): #メモを保存または更新する関数
    with DatabaseConnection(MEMO_DATABASE) as cursor:
        cursor.execute("SELECT * FROM memo")
        existing_memo = cursor.fetchone()
        if existing_memo:
            cursor.execute("UPDATE memo SET content=?", (content,))
        else:
            cursor.execute("INSERT INTO memo (content) VALUES (?)", (content,))

@app.route('/', methods=['GET', 'POST']) #トップページのルート
def index():
    result = None
    histories = fetch_histories()
    memo_content = fetch_memo_content()
    if request.method == 'POST':
        probability = float(request.form.get('probability')) / 100 
        times = int(request.form.get('times'))
        success_probability = calculate_probability(probability, times)
        result = round(success_probability * 100, 8)
        save_history(probability * 100, times, result)
        flash('計算結果を履歴に保存しました。', 'success')
        return redirect(url_for('index'))
    return render_template('index.html', result=result, histories=histories, memo_content=memo_content)

@app.route('/delete/<int:entry_id>', methods=['GET'])#履歴エントリの削除用のルート
def delete_entry(entry_id):
    if not entry_exists(entry_id):
        flash('該当の履歴エントリが見つかりません。', 'danger')
        return redirect(url_for('index'))
    with DatabaseConnection() as cursor:
        cursor.execute("DELETE FROM history WHERE id=?", (entry_id,))
    flash('履歴エントリを削除しました。', 'success')
    return redirect(url_for('index'))

@app.route('/add_memo', methods=['POST'])#メモの追加・更新用のルート
def add_memo():
    content = request.form.get('memo_content')
    save_or_update_memo(content)
    flash('メモを保存しました。', 'success')
    return redirect(url_for('index'))

def calculate_probability(input_probability, times):#ガチャの成功確率を計算する関数
    calculated_probability = 1 - (1 - input_probability)**times
    max_probability = 0.9999999999
    if calculated_probability > max_probability:
        calculated_probability = max_probability
    return calculated_probability


if __name__ == '__main__':
    app.run(debug=True)