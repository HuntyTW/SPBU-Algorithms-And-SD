import pandas as pd
import numpy as np

def run_tests(file_path='dataset.xlsx'):
    print(f"--- Запуск тестов для файла: {file_path} ---\n")
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"[ОШИБКА] Файл {file_path} не найден. Убедитесь, что он находится в одной папке со скриптом.")
        return
    except Exception as e:
        print(f"[ОШИБКА] Не удалось прочитать файл: {e}")
        return

    # 1. Общее количество строк
    print(f"1. Общее количество строк: {len(df)}")

    # 2 & 3. Уникальность паспортов и СНИЛС, неизменность у пациента
    fio_per_passport = df.groupby('Паспортные данные')['ФИО'].nunique()
    snils_per_passport = df.groupby('Паспортные данные')['СНИЛС'].nunique()
    fio_per_snils = df.groupby('СНИЛС')['ФИО'].nunique()

    if (fio_per_passport > 1).any() or (snils_per_passport > 1).any() or (fio_per_snils > 1).any():
        print("2-3. [ОШИБКА] Паспорт или СНИЛС меняются у одного и того же пациента при повторных визитах.")
    else:
        print("2-3. [УСПЕХ] Паспорта и СНИЛС уникальны и не меняются у одного и того же пациента.")

    # 4. Даты визитов и анализов попадают в рабочие дни и часы
    df['Дата посещения врача'] = pd.to_datetime(df['Дата посещения врача'])
    df['Дата получения анализов'] = pd.to_datetime(df['Дата получения анализов'])

    visit_wd = df['Дата посещения врача'].dt.dayofweek
    visit_h = df['Дата посещения врача'].dt.hour
    analysis_wd = df['Дата получения анализов'].dt.dayofweek
    analysis_h = df['Дата получения анализов'].dt.hour

    wd_ok = (visit_wd.between(0, 4)).all() and (analysis_wd.between(0, 4)).all()
    wh_ok = (visit_h.between(8, 17)).all() and (analysis_h.between(8, 17)).all()

    if wd_ok and wh_ok:
        print("4. [УСПЕХ] Все даты попадают в рабочие дни (Пн-Пт) и часы (08:00-17:59).")
    else:
        print("4. [ОШИБКА] Найдены записи вне рабочих дней или часов.")

    # 5. Интервал между визитом и анализами — от 24 до 72 часов
    delta_va = (df['Дата получения анализов'] - df['Дата посещения врача']).dt.total_seconds() / 3600
    if (delta_va >= 24).all() and (delta_va <= 72).all():
        print("5. [УСПЕХ] Интервал между визитом и анализами строго от 24 до 72 часов.")
    else:
        errors_count = (~delta_va.between(24, 72)).sum()
        print(f"5. [ОШИБКА/ПРЕДУПРЕЖДЕНИЕ] Нарушен интервал 24-72ч в {errors_count} строках.")

    # 6. Между анализами и следующим визитом проходит не меньше 24 часов
    df = df.sort_values(by=['Паспортные данные', 'Дата посещения врача'])
    df['Следующий визит'] = df.groupby('Паспортные данные')['Дата посещения врача'].shift(-1)
    
    valid_next_visits = df.dropna(subset=['Следующий визит'])
    delta_an = (valid_next_visits['Следующий визит'] - valid_next_visits['Дата получения анализов']).dt.total_seconds() / 3600
    
    if (delta_an >= 24).all() or len(valid_next_visits) == 0:
        print("6. [УСПЕХ] Между анализами и следующим визитом всегда проходит не менее 24 часов.")
    else:
        errors_an_count = (delta_an < 24).sum()
        print(f"6. [ОШИБКА] Найдено {errors_an_count} случаев, когда до следующего визита прошло менее 24 часов.")

    # 7. Ни одна карта не использована больше 5 раз
    card_uses = df['Карта оплаты'].value_counts()
    if (card_uses <= 5).all():
        print("7. [УСПЕХ] Ни одна карта не использована более 5 раз.")
    else:
        print(f"7. [ОШИБКА] Найдены карты, использованные более 5 раз. Максимум использований: {card_uses.max()}.")
        
    print("\n--- Проверка завершена ---")

if __name__ == '__main__':
    run_tests()