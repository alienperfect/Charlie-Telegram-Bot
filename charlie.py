from constants import API_KEY, TOKEN
import requests
import sqlite3
from sqlite3.dbapi2 import Error, IntegrityError, OperationalError
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


class Database():
    def __init__(self):
        self.connection = sqlite3.connect(
            'data.db',
            check_same_thread=False
            )
        self.cursor = self.connection.cursor()

    def add_word(self, word, synonyms, update):
        self.connection.execute(
            '''CREATE TABLE IF NOT EXISTS words(
                word text,
                synonyms text,
                CONSTRAINT unique_data UNIQUE (word, synonyms)
                )'''
            )
        try:
            self.cursor.execute(
                '''INSERT INTO words VALUES (?, ?)''',
                [word, synonyms]
                )
            self.connection.commit()
            print('Successfully added.')
            self.get_synonyms_from_db(word, update)
        except IntegrityError:
            print('This word already in a list.')
        except Error as e:
            print(f'Error "{e}" occured while inserting data.')

    def check_word(self, word):
        try:
            self.cursor.execute('SELECT * FROM words WHERE word=?', [word])
            result = self.cursor.fetchone()
            if result == None:
                print('No word here...')
                return True
            else:
                print('Found the word!')
                return False
        except OperationalError:
            return True

    def get_synonyms_from_db(self, word, update):
        try:
            self.cursor.execute('SELECT synonyms FROM words WHERE word=?', [word])
            result = self.cursor.fetchall()
            print(result)
            synonyms = result[0][0]
            print('from database:')
            print(synonyms)
            update.message.reply_text(
                f'Synonyms of <b>{word}</b>:\n\n'
                f'{synonyms}'
                '.',
                parse_mode='HTML'
            )
        except Error as e:
            update.message.reply_text(
                f'Error {e} has occured.'
            )


class API():
    def get_synonyms(self, update, context):
        word = update['message']['text']
        word = word.lower()
        print(word)

        call = db.check_word(word)
        if call == True:
            response = requests.get(
                f'https://www.dictionaryapi.com/api/v3/references/thesaurus/json/{word}?key={API_KEY}'
                )
            if response:
                print('Success!')
            else:
                return print('An error occured.')

            content = response.json()

            try:
                result = [*content[0]['meta']['syns'][0]]
            except:
                possible = ', '.join(content)
                return update.message.reply_text(
                    f"Didn't catch that word. Maybe you meant:\n\n"
                    f'{possible}?'
                    )

            synonyms = [i for i in result]
            synonyms = ', '.join(synonyms)

            print('from request:')
            print(synonyms)

            db.add_word(word, synonyms, update)
        else:
            return db.get_synonyms_from_db(word, update)


db = Database()
api = API()


def main():
    charlie = Updater(TOKEN)
    dispatcher = charlie.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, api.get_synonyms))

    charlie.start_polling()


if __name__ == '__main__':
    main()
