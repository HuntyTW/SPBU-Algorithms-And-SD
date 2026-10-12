import pandas as pd
import openpyxl
import random
from collections import Counter

df = pd.read_excel('dataset.xlsx')

def generate_id(values, prefix):
    uniq = list(values.unique())
    nums = random.sample(range(100000, 100000 + len(uniq) * 10), len(uniq))
    return {v: f"{prefix}{n}" for v, n in zip(uniq, nums)}

def pseudonymize(df):
    client_map = generate_id(df["СНИЛС"], "C")

    df = df.copy()
    df["ID клиента"] = df["СНИЛС"].map(client_map)

    key = df[["ID клиента", "ФИО", "Паспортные данные", "СНИЛС", "Карта оплаты"]].drop_duplicates()

    first = ["ID клиента"]
    df = df[first + [c for c in df.columns if c not in first]]
    df = df.drop(columns=["ФИО", "Паспортные данные", "СНИЛС", "Карта оплаты"])
    return df, key

anon_df, key = pseudonymize(df)

key.to_excel("key.xlsx", index=False)

QI_COLUMNS = [
    "Симптомы",
    "Выбор врача",
    "Дата посещения врача",
    "Анализы",
    "Дата получения анализов",
    "Стоимость анализов",
]

def ask_quasi_identifiers():
    print("Столбцы:")
    for i, col in enumerate(QI_COLUMNS, 1):
        print(f"{i}. {col}")
    while True:
        raw = input("Номера квази-идентификаторов через пробел: ").split()
        if raw and all(x.isdigit() and 1 <= int(x) <= len(QI_COLUMNS) for x in raw):
            return [QI_COLUMNS[n - 1] for n in sorted(set(map(int, raw)))]
        print(f"Нужно ввести хотя бы один номер от 1 до {len(QI_COLUMNS)}")

qi = ask_quasi_identifiers()

def k_anonimity(anon_df, qi):
    k_anonimity_dict = {}
    
    for row in zip(*(df[qi_column] for qi_column in qi)):
        if row not in k_anonimity_dict:
            k_anonimity_dict[row] = 1
        else:
            k_anonimity_dict[row] += 1

    k = min(k_anonimity_dict.values())
    
    cnt = Counter(k_anonimity_dict)
    
    unique_rows = []
    for row in zip(df.itertuples(), *(df[qi_column] for qi_column in qi)):
        if k_anonimity_dict[row[1::]] == 1:
            unique_rows.append(row)
