import math
import sys

def parse_items(value):
    """Извлекает и очищает элементы из списка, кортежа или строки с запятыми."""
    items = set()
    if isinstance(value, (list, tuple, set)):
        for item in value:
            if isinstance(item, str) and item.strip():
                items.add(item.strip())
    elif isinstance(value, str):
        for item in value.split(','):
            if item.strip():
                items.add(item.strip())
    return items

def extract_unique_symptoms_and_analyses(data_module):
    """Находит двумерный список в модуле data и обходит все записи врачей."""
    dataset = None
    
    # 1. Поиск двумерного списка среди основных возможных названий переменных
    for attr in ['DATA', 'DOCTORS', 'DOCTORS_DATA', 'data', 'doctors', 'SPECIALISTS', 'specialists']:
        if hasattr(data_module, attr):
            val = getattr(data_module, attr)
            if isinstance(val, (list, tuple)):
                dataset = val
                break
                
    # 2. Если по имени не нашли, ищем любой первый список списков/словарей в модуле
    if dataset is None:
        for attr in dir(data_module):
            if not attr.startswith('__'):
                val = getattr(data_module, attr)
                if isinstance(val, (list, tuple)) and len(val) > 0 and isinstance(val[0], (list, tuple, dict)):
                    dataset = val
                    break

    if dataset is None:
        print("[ОШИБКА] Не удалось найти двумерный список с данными врачей в data.py.")
        sys.exit(1)

    unique_symptoms = set()
    unique_analyses = set()

    # Обход двумерного списка
    for row in dataset:
        if isinstance(row, dict):
            # Если каждая строка представлена словарем
            for k, v in row.items():
                k_lower = str(k).lower()
                if 'симптом' in k_lower or 'symptom' in k_lower:
                    unique_symptoms.update(parse_items(v))
                elif 'анализ' in k_lower or 'analyses' in k_lower:
                    unique_analyses.update(parse_items(v))
        elif isinstance(row, (list, tuple)):
            # Если строка — список [врач, симптомы, анализы]
            sub_collections = []
            for item in row:
                if isinstance(item, (list, tuple, set)):
                    sub_collections.append(item)
                elif isinstance(item, str) and ',' in item:
                    sub_collections.append(item)

            if len(sub_collections) >= 2:
                unique_symptoms.update(parse_items(sub_collections[0]))
                unique_analyses.update(parse_items(sub_collections[1]))
            elif len(row) >= 3:
                unique_symptoms.update(parse_items(row[1]))
                unique_analyses.update(parse_items(row[2]))

    return unique_symptoms, unique_analyses

def count_combinations(n: int, max_k: int) -> int:
    """Вычисляет сумму сочетаний C(n, k) от 1 до max_k."""
    return sum(math.comb(n, k) for k in range(1, min(n, max_k) + 1))

def main():
    try:
        import data
    except ImportError:
        print("[ОШИБКА] Файл data.py не найден. Поместите скрипт в одну папку с data.py.")
        sys.exit(1)

    symptoms, analyses = extract_unique_symptoms_and_analyses(data)

    n_symptoms = len(symptoms)
    n_analyses = len(analyses)

    total_symptoms_comb = count_combinations(n_symptoms, 10)
    total_analyses_comb = count_combinations(n_analyses, 5)

    print("=== АНАЛИЗ ДАННЫХ ИЗ data.py ===")
    print(f"Всего уникальных симптомов (N): {n_symptoms}")
    print(f"Всего уникальных анализов  (M): {n_analyses}\n")

    print(f"Максимальное число комбинаций симптомов (до 10): {total_symptoms_comb}")
    print(f"Максимальное число комбинаций анализов (до 5):  {total_analyses_comb}\n")

    print("--- РЕЗУЛЬТАТЫ ПРОВЕРКИ ---")

    if total_symptoms_comb > 5000:
        print(f"[УСПЕХ] Комбинаций симптомов ({total_symptoms_comb}) > 5000")
    else:
        print(f"[ОШИБКА] Комбинаций симптомов ({total_symptoms_comb}) <= 5000 (требуется > 5000)")

    if total_analyses_comb > 250:
        print(f"[УСПЕХ] Комбинаций анализов ({total_analyses_comb}) > 250")
    else:
        print(f"[ОШИБКА] Комбинаций анализов ({total_analyses_comb}) <= 250 (требуется > 250)")

if __name__ == '__main__':
    main()