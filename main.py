# Импорт необходимых библиотек
from selenium import webdriver  # Инструмент для автоматизации веб-браузера
from selenium.webdriver.chrome.options import Options  # Опции для настройки веб-браузера Chrome
from selenium.webdriver.common.by import By  # Методы для поиска элементов на веб-странице
from selenium.webdriver.chrome.service import Service  # Сервис для управления драйвером браузера Chrome
import pandas as pd  # Библиотека для работы с данными в формате таблицы
from time import sleep  # Метод для ожидания в течение определенного времени


# Функция для создания DataFrame с данными о матчах для определенного вида спорта
def create_df(sport, params):
    # Настройка параметров веб-браузера Chrome
    custom_options = Options()
    custom_options.add_argument("--start-maximized")  # Максимизация окна браузера

    # Путь к исполняемому файлу драйвера Chrome
    path_driver = "/usr/local/bin/chromedriver"

    # Создание сервиса для драйвера Chrome
    service = Service(path_driver)

    # Инициализация экземпляра Chrome WebDriver с настроенными параметрами и сервисом
    driver = webdriver.Chrome(service=service, options=custom_options)

    # Ссылка на веб-сайт FlashScore
    link = "https://www.flashscore.com.ua/"
    driver.get(link)

    # Словарь для соответствия названий видов спорта и их индексов на веб-странице
    dict_ = {
        'ИЗБРАННОЕ': 0,
        'ФУТБОЛ': 1,
        'ХОККЕЙ': 2,
        'ТЕННИС': 3,
        'БАСКЕТБОЛ': 4,
        'ВОЛЕЙБОЛ': 5,
        'ГАНДБОЛ': 6
    }

    # Переход к выбранной категории спорта
    driver_m = driver.find_elements(By.CLASS_NAME, 'menuTop__text')[dict_[sport]].click()

    # Поиск всех матчей выбранного вида спорта
    matches = driver.find_elements(By.CLASS_NAME, 'event__match.event__match--twoLine')

    # Список для хранения идентификаторов матчей
    ids = []
    final = []

    # Извлечение идентификаторов матчей с веб-страницы
    for id in matches:
        full_id = id.get_attribute('id')
        cleaned_id = full_id[4:]
        ids.append(cleaned_id)

    # Обход каждого идентификатора матча
    for match_id in ids:
        # Формирование URL для статистики матча
        url_match_statistics = f'https://www.flashscore.com.ua/match/{match_id}/#/match-summary/match-statistics/0'
        driver.get(url_match_statistics)
        sleep(5)

        # Извлечение деталей матча
        league = driver.find_elements(By.CLASS_NAME, 'tournamentHeader__country')[0].text
        team_1 = driver.find_elements(By.CLASS_NAME, 'duelParticipant__home')[0].text
        team_2 = driver.find_elements(By.CLASS_NAME, 'duelParticipant__away')[0].text
        date = driver.find_elements(By.CLASS_NAME, 'duelParticipant__startTime')[0].text
        status = driver.find_elements(By.CLASS_NAME, 'detailScore__status')[0].text
        score = driver.find_elements(By.CLASS_NAME, 'detailScore__wrapper')[0].text.splitlines()[::2]

        # Если матч еще не начался, установить счет '-'
        if status == 'not started':
            score = ['-', '-']

        # Извлечение элементов статистики
        statistics_elements = driver.find_elements(By.CLASS_NAME, '_row_rz3ch_9')

        statistics_dict = {}

        # Обход элементов статистики и заполнение словаря
        for element in statistics_elements:
            static = element.text.splitlines()
            key = static[1]
            value_host = static[0]
            value_guest = static[-1]
            if key in params:
                statistics_dict[key] = [value_host, value_guest]

        # Заполнение отсутствующих статистических данных '-'
        for param in params:
            if param not in statistics_dict:
                statistics_dict[param] = ['-', '-']

        # Создание DataFrame для информации о матче
        match_info_df = pd.DataFrame([[league, date, status, team_1, team_2, score[0], score[-1]]],
                                     columns=['Лига', 'Дата', 'Статус', 'Хозяева', 'Гости', 'Счет хозяев',
                                              'Счет гостей'])

        # Создание DataFrame для статистики матча
        df = pd.DataFrame(statistics_dict)

        # Извлечение информации о домашней и гостевой командах, и объединение DataFrame
        home_info = df.loc[[0]]
        home_info = home_info.add_suffix('_home')
        away_info = df.loc[[1]]
        away_info = away_info.add_suffix('_away')
        away_info = away_info.reset_index(drop=True)

        final_dop_info = pd.merge(home_info, away_info, left_index=True, right_index=True)
        final_stat = pd.merge(match_info_df, final_dop_info, left_index=True, right_index=True)

        final.append(final_stat)

    # Закрытие WebDriver Chrome
    driver.quit()
    return final


# Основная функция
def main():
    sport = 'ХОККЕЙ'  # Выбранный вид спорта
    param = ['Броски в створ ворот', 'Удаления']  # Параметры статистики
    final = create_df(sport, param)  # Получение DataFrame с данными о матчах
    final_df = pd.concat(final)  # Объединение всех DataFrame в один
    excel_filename = "output_data.xlsx"  # Название файла Excel для вывода
    final_df.to_excel(excel_filename, index=False)  # Запись DataFrame в файл Excel


# Выполнение основной функции, если скрипт запущен напрямую
if __name__ == '__main__':
    main()
