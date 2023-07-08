# Импортируем необходимые библиотеки
import streamlit as st
from PIL import Image
from urllib.request import urlopen
from io import BytesIO

# Импортируем классы из файла exercise_generator
from exercise_generator import TextToDataFrame, DictionaryCreator, ExerciseGenerator

# Задаем ключ API для доступа к словарю
api_key = 'dict.1.1.20230629T105549Z.fb37ebf7609e3a28.23abdd368ee0f4b1fe26c9f8d9b4d3097fab27a7'

# Определяем функцию для загрузки данных из текста
# @st.cache
def creating_a_dictionary_and_exercises(text):
    """
    Функция для загрузки данных из текста.

    Аргументы:
    text - текст для обработки.

    Возвращает:
    Кортеж из двух датафреймов:
    - Датафрейм с упражнениями по английскому языку.
    - Датафрейм со словарем.
    """
    # Создаем объект класса TextToDataFrame
    text_to_df = TextToDataFrame(text)

    # Преобразуем текст в датафрейм с упражнениями
    english_exercises_df = text_to_df.txt_to_df()

    # Создаем объект класса DictionaryCreator
    dictionary_creator = DictionaryCreator(api_key)

    # Создаем датафрейм со словарем
    dictionary_df = dictionary_creator.create_dictionary_df(english_exercises_df)

    # Создаем объект класса ExerciseGenerator
    exercise_generator = ExerciseGenerator()

    # Генерируем случайные упражнения
    english_exercises_df = exercise_generator.generate_random_exercises(english_exercises_df)

    # Возвращаем датафреймы с упражнениями и словарем
    return english_exercises_df, dictionary_df


# Создаем виджет для загрузки файлов
uploaded_file = st.file_uploader("Загрузите текстовый файл", type=["txt"])

# Проверяем, был ли загружен файл
if uploaded_file is not None:
    # Читаем содержимое файла и преобразуем его в строку
    text = uploaded_file.read().decode()

    # Загружаем данные из текста
    english_exercises_df, dictionary_df = creating_a_dictionary_and_exercises(text)

    # Отображаем изображение в шапке страницы
    img_url = "https://climbingthedissertationmountain.files.wordpress.com/2018/01/cropped-vladislav-klapin-316711.jpg"
    image_data = urlopen(img_url).read()
    header_image = Image.open(BytesIO(image_data))
    st.image(header_image, use_column_width=True)

    # Отображаем датафрейм со словарем на странице
    st.dataframe(dictionary_df, height=300, width=900)

    # Получаем список типов упражнений из датафрейма с упражнениями
    exercise_types = english_exercises_df["exercise_type"].unique().tolist()

    # Создаем виджет для выбора типов упражнений в боковой панели
    selected_types = st.sidebar.multiselect("Выберите типы упражнений", exercise_types)

    # Фильтруем датафрейм с упражнениями по выбранным типам упражнений
    if not selected_types:
        filtered_df = english_exercises_df.copy()
    else:
        filtered_df = english_exercises_df[english_exercises_df["exercise_type"].isin(selected_types)]

    # Получаем общее количество упражнений в отфильтрованном датафрейме
    total_exercises = len(filtered_df)

    # Получаем текущий индекс и текущий счет из состояния сессии (или задаем значения по умолчанию)
    current_index = st.session_state.get("current_index", 0)
    current_score = st.session_state.get("current_score", 0)

    # Создаем виджет для отображения прогресса выполнения упражнений в боковой панели
    progress_bar = st.sidebar.progress(current_score / total_exercises)

    # Создаем пустой элемент для отображения текущего счета в боковой панели
    score_text = st.sidebar.empty()

    # Отображаем текущий счет в пустом элементе
    score_text.text(f"Решено {current_score} из {total_exercises} упражнений")

    # Отображаем 5 упражнений на странице
    correct_answers = 0
    for i in range(5):

        # Проверяем, есть ли еще упражнения для отображения
        if current_index + i < total_exercises:

            # Отображаем номер упражнения
            st.markdown(f"**Упражнение {current_index + i + 1}**")

            # Получаем тип упражнения из датафрейма
            exercise_type = filtered_df.iloc[current_index + i]["exercise_type"]

            # Отображаем тип упражнения
            st.write(f"Тип упражнения: {exercise_type}")

            # Получаем предложение для упражнения из датафрейма
            exercise_sentence = filtered_df.iloc[current_index + i]["exercise_sentence"]

            # Выделяем пропущенное слово красным цветом
            highlighted_sentence = exercise_sentence.replace("**",
                                                             "<span style='border: 2px solid red;'>",
                                                             1).replace("**", "</span>", 1)

            # Отображаем предложение для упражнения с выделенным пропущенным словом
            st.markdown(f"{highlighted_sentence}", unsafe_allow_html=True)

            # Получаем варианты ответов из датафрейма
            options = filtered_df.iloc[current_index + i]["options"]

            # Добавляем пустой вариант ответа в начало списка
            options.insert(0, "")

            # Создаем выпадающий список с вариантами ответов
            selectbox = st.selectbox(f"Выберите верный ответ", options, key=f"selectbox_{i}")

            # Получаем правильный ответ из датафрейма
            correct_answer = filtered_df.iloc[current_index + i]["correct_answer"]

            # Проверяем, выбрал ли пользователь вариант ответа
            if selectbox:

                # Проверяем, верный ли выбранный вариант ответа
                if selectbox == correct_answer:

                    # Отображаем сообщение об успехе
                    st.success("✅ Верно!")

                    # Увеличиваем счет на 1
                    current_score += 1

                    # Обновляем прогресс выполнения упражнений
                    progress_bar.progress(current_score / total_exercises)

                    # Обновляем отображение текущего счета
                    score_text.text(f"Решено {current_score} из {total_exercises} упражнений")

                    # Увеличиваем счетчик правильных ответов на 1
                    correct_answers += 1

                else:
                    # Отображаем сообщение об ошибке
                    st.error("❌ Неверно!")

                    # Отображаем правильный ответ
                    st.write(f"Правильный ответ: {correct_answer}")

        else:
            break

    # Проверяем, правильно ли решены все 5 упражнений на странице
    if correct_answers == 5:
        # Запускаем анимацию воздушных шаров
        st.balloons()

    # Проверяем, есть ли еще упражнения для отображения на следующей странице
    if current_index + 5 < total_exercises:

        # Создаем кнопку для перехода к следующим 5 упражнениям
        if st.button("Следующие 5 упражнений"):
            # Увеличиваем текущий индекс на 5
            current_index += 5

            # Сохраняем текущий индекс в состоянии сессии
            st.session_state["current_index"] = current_index

            # Сохраняем текущий счет в состоянии сессии
            st.session_state["current_score"] = current_score

            # Перезапускаем приложение
            st.experimental_rerun()

    else:
        # Отображаем сообщение об окончании упражнений
        st.write("Поздравляем! Вы решили все упражнения!")

        # Отображаем итоговый счет
        st.write(f"Ваш итоговый счет: {current_score} из {total_exercises}")

        # Создаем кнопку для начала заново
        if st.button("Начать заново"):
            # Очищаем состояние сессии
            st.session_state.clear()

            # Перезапускаем приложение
            st.experimental_rerun()
