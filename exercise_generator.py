import pandas as pd
import spacy
import string
import os

from nltk.tokenize import sent_tokenize
from googletrans import Translator
from word_forms.word_forms import get_word_forms

import random
import gensim.downloader as api

import requests

# Предобученная модель spacy
model_dir = 'C:\Users\matro\anaconda3\lib\site-packages'
model_name = 'en_core_web_sm'
model_path = os.path.join(model_dir, model_name)

nlp = spacy.load(model_path)

# Предобученная модель word2vec-ruscorpora-300 c gensim
modelru = api.load("word2vec-ruscorpora-300")


class TextToDataFrame:
    def __init__(self, text):
        """
        Конструктор класса TextToDataFrame.

        Аргументы:
        text - текст для обработки.
        """
        self.text = text

    def txt_to_df(self):
        """
        Метод для преобразования текста в датафрейм.

        Возвращает:
        Датафрейм, содержащий предложения из текста и дополнительные столбцы
        для упражнений по английскому языку.
        """
        # Разбиваем текст на предложения
        sentences = sent_tokenize(self.text)

        # Удаляем пробелы и табуляции в начале и в конце каждого предложения
        sentences = [sentence.strip() for sentence in sentences]

        # Создаем датафрейм из списка предложений
        df = pd.DataFrame(sentences, columns=['sentence'])

        # Добавляем новые столбцы в датафрейм
        df['exercise_type'] = ''
        df['exercise_sentence'] = ''
        df['options'] = ''
        df['correct_answer'] = ''

        return df


class DictionaryCreator:
    def __init__(self, api_key):
        """
        Конструктор класса DictionaryCreator.
        
        Аргументы:
        api_key - API-ключ для доступа к сервису Yandex Dictionary.
        """
        self.api_key = api_key
    
    def get_transcription(self, word):
        """
        Метод для получения транскрипции слова с помощью API сервиса Yandex Dictionary.
        
        Аргументы:
        word - слово для транскрипции.
        
        Возвращает:
        Транскрипцию слова или None, если транскрипция не найдена.
        """
        # URL для запроса к API сервиса Yandex Dictionary
        url = f"https://dictionary.yandex.net/api/v1/dicservice.json/lookup?key={self.api_key}&lang=en-ru&text={word}"

        # Отправляем запрос к API сервиса Yandex Dictionary
        response = requests.get(url)

        # Проверяем статус ответа
        if response.status_code == 200:
            # Получаем JSON-ответ
            data = response.json()

            # Получаем список элементов с транскрипциями
            transcription_elements = data.get('def', [])

            # Проверяем, найден ли хотя бы один элемент
            if len(transcription_elements) > 0:
                # Получаем первый элемент списка
                transcription_element = transcription_elements[0]

                # Получаем текст элемента
                transcription = transcription_element.get('ts')

                return transcription
            else:
                # Если элемент не найден, возвращаем None
                return None
        else:
            # Если статус ответа не равен 200, возвращаем None
            return None
    
    def create_dictionary_df(self, df, min_word_length=6):
        """
        Метод для создания датафрейма со словами, их транскрипциями и переводами из другого датафрейма.
        
        Аргументы:
        df - датафрейм с предложениями для анализа.
        min_word_length - минимальная длина слова, слова короче этой длины не будут включены в датафрейм.
        
        Возвращает:
        Датафрейм, где первая колонка - это сложные слова, вторая колонка - транскрипции слов, 
        а третья колонка - переводы на русский язык.
        """
        # Создаем пустой список для хранения данных
        data = []

        # Создаем множество для хранения уникальных слов
        unique_words = set()

        # Создаем объект Translator
        translator = Translator()

        # Получаем список предложений из датафрейма
        sentences = df['sentence'].tolist()

        for sentence in sentences:
            # Удаляем знаки препинания из предложения
            sentence = sentence.translate(str.maketrans('', '', string.punctuation))

            # Разбиваем предложение на слова
            words = sentence.split()

            for word in words:

                # Определяем длину слова
                word_length = len(word)

                # Если длина слова больше или равна минимальной
                if word_length >= min_word_length:

                    # Проверяем, есть ли уже такое слово в множестве
                    if word not in unique_words:

                        # Добавляем слово в множество
                        unique_words.add(word)

                        # Получаем перевод слова
                        translation = translator.translate(word, src='en', dest='ru').text

                        # Получаем транскрипцию слова
                        transcription = self.get_transcription(word)

                        # Добавляем данные в список
                        data.append((word.capitalize(), transcription, translation.capitalize()))

        # Создаем датафрейм из списка данных
        result_df = pd.DataFrame(data, columns=['Word', 'Transcription', 'Translation'])
        result_df = result_df.dropna()
        result_df = result_df.reset_index(drop=True)

        return result_df


class ExerciseGenerator:
    def generate_translate_exercise(self, row):
        """
        Функция для генерации упражнения на перевод слова.
    
        Аргументы:
        row - строка датафрейма, содержащая предложение и столбцы для упражнений.
    
        Возвращает:
        Обновленную строку с информацией об упражнении на перевод слова.
        """
        # Получаем предложение
        sentence = row['sentence']
    
        # Разбиваем предложение на токены с помощью spacy
        doc = nlp(sentence)
    
        # Выбираем токены, которые являются существительными или прилагательными
        tokens = [token for token in doc if token.pos_ in ['NOUN', 'ADJ']]
    
        # Если есть подходящие токены
        if len(tokens) > 0:
            # Выбираем случайный токен
            token = random.choice(tokens)
        
            # Получаем текст токена
            token_text = token.text
        
            # Выделяем выбранное слово жирным шрифтом
            exercise_sentence = sentence.replace(token_text, f'**{token_text}**')
        
            # Проверяем, начинается ли слово с заглавной буквы
            is_title = token_text.istitle()
        
            # Преобразуем слово в нижний регистр для поиска похожих слов в модели word2vec
            token_text = token_text.lower()
        
            # Находим перевод выбранного слова
            translator = Translator()
            translation = translator.translate(token_text, src='en', dest='ru').text

            try:
                # Получаем ближайшие слова из модели word2vec
                pos_map = {'NOUN': 'NOUN', 'ADJ': 'ADJ'}
                key = f"{translation}_{pos_map[token.pos_]}"
                similar_words = modelru.most_similar(key, topn=3)
            
                # Выбираем два ближайших слова из списка ближайших слов и удаляем приписки _NOUN и _ADJ
                options = [word.split('_')[0] for word, similarity in similar_words 
                           if word.endswith(pos_map[token.pos_]) and '::' not in word]

                # Если слово начиналось с заглавной буквы, преобразуем перевод в заглавный
                if is_title:
                    options = [option.title() for option in options]
                    translation = translation.title()
                
                # Добавляем перевод верного ответа в список вариантов
                options.append(translation)
            
                # Удаляем дубликаты из списка вариантов
                options = list(set(options))
            
                # Перемешиваем список вариантов
                random.shuffle(options)
            
                # Обновляем строку с информацией об упражнении
                row['exercise_type'] = 'Выберите перевод слова'
                row['exercise_sentence'] = exercise_sentence
                row['options'] = options
                row['correct_answer'] = translation
        
            except KeyError:
                # Если нет подходящих слов в модели, заполняем все поля None
                row['exercise_type'] = None
                row['exercise_sentence'] = None
                row['options'] = None
                row['correct_answer'] = None
    
        else:
            # Если нет подходящих токенов, заполняем все поля None
            row['exercise_type'] = None
            row['exercise_sentence'] = None
            row['options'] = None
            row['correct_answer'] = None
    
        return row


    def generate_verb_exercise(self, row):
        """
        Функция для генерации упражнения с глаголами.
    
        Аргументы:
        row - строка датафрейма, содержащая предложение и столбцы для упражнений.
    
        Возвращает:
        Обновленную строку с информацией об упражнении с глаголами.
        """
        # Получаем предложение
        sentence = row['sentence']
    
        # Разбиваем предложение на токены с помощью spacy
        doc = nlp(sentence)
    
        # Выбираем токены, которые являются глаголами
        tokens = [token for token in doc if token.pos_ == 'VERB']
    
        # Если есть подходящие токены
        if len(tokens) > 0:
            # Выбираем случайный токен
            token = random.choice(tokens)
        
            # Получаем текст токена
            token_text = token.text
        
            # Заменяем токен на пропуск в предложении
            start = token.idx
            end = start + len(token)
            exercise_sentence = sentence[:start] + '___' + sentence[end:]
        
            # Получаем верный ответ
            correct_answer = token_text
        
            # Проверяем, начинается ли слово с заглавной буквы
            is_title = token_text.istitle()
        
            # Преобразуем слово в нижний регистр для получения других форм глагола
            token_text = token_text.lower()
        
            # Получаем другие формы глагола
            word_forms = get_word_forms(token_text)
        
            # Получаем список форм глагола
            verb_forms = list(word_forms['v'])

            # Используем все формы глагола из списка
            options = verb_forms
        
            # Если слово начиналось с заглавной буквы, преобразуем варианты в заглавные
            if is_title:
                options = [option.title() for option in options]
        
            # Перемешиваем список вариантов
            random.shuffle(options)
        
            # Обновляем строку с информацией об упражнении
            row['exercise_type'] = 'Выберите форму глагола'
            row['exercise_sentence'] = exercise_sentence
            row['options'] = options
            row['correct_answer'] = correct_answer
    
        else:
            # Если нет подходящих токенов, заполняем все поля None
            row['exercise_type'] = None
            row['exercise_sentence'] = None
            row['options'] = None
            row['correct_answer'] = None
    
        return row
    
    def generate_article_exercise(self, row):
        """
        Функция для генерации упражнения на употребление артиклей.
    
        Аргументы:
        row - строка датафрейма, содержащая предложение и столбцы для упражнений.
    
        Возвращает:
        Обновленную строку с информацией об упражнении на употребление артиклей.
        """
        # Получаем предложение
        sentence = row['sentence']
    
        # Разбиваем предложение на токены с помощью spacy
        doc = nlp(sentence)
    
        # Выбираем токены, которые являются артиклями
        tokens = [token for token in doc if token.pos_ == 'DET' and token.text.lower() in ['a', 'an', 'the']]
    
        # Если есть подходящие токены
        if len(tokens) > 0:
            # Выбираем случайный токен
            token = random.choice(tokens)
        
            # Получаем текст токена
            token_text = token.text
        
            # Проверяем, начинается ли слово с заглавной буквы
            is_title = token_text.istitle()
        
            # Заменяем токен на пропуск в предложении
            start = token.idx
            end = start + len(token)
            exercise_sentence = sentence[:start] + '___' + sentence[end:]
        
            # Получаем верный ответ
            correct_answer = token_text
        
            # Создаем список вариантов ответа
            options = ['a', 'an', 'the']
        
            # Если слово начиналось с заглавной буквы, преобразуем варианты в заглавные
            if is_title:
                options = [option.title() for option in options]
        
            # Обновляем строку с информацией об упражнении
            row['exercise_type'] = 'Выберите артикль'
            row['exercise_sentence'] = exercise_sentence
            row['options'] = options
            row['correct_answer'] = correct_answer
    
        else:
            # Если нет подходящих токенов, заполняем все поля None
            row['exercise_type'] = None
            row['exercise_sentence'] = None
            row['options'] = None
            row['correct_answer'] = None
    
        return row
    
    def generate_random_exercises(self, df):
        """
        Метод для генерации случайных упражнений.
        
        Аргументы:
        df - датафрейм, содержащий предложения и столбцы для упражнений.
        
        Возвращает:
        Обновленный датафрейм с информацией об упражнениях.
        """
        for i, row in df.iterrows():
            # Выбираем случайную функцию генерации упражнений
            exercise_function = random.choice([self.generate_translate_exercise,
                                               self.generate_verb_exercise,
                                               self.generate_article_exercise])

            # Применяем функцию генерации упражнений к строке
            row = exercise_function(row)

            # Обновляем строку в датафрейме
            df.iloc[i] = row

        # Удаляем пустые строки и сбрасываем индексы
        df = df.dropna()
        df = df.reset_index(drop=True)

        return df
