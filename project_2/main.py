import pandas as pd
import openpyxl
import random
from collections import Counter
from functools import lru_cache
from data_group import DOCTOR_PROFILES, classify_research
import numpy as np

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

def k_anonimity(table, qi, flag=False):
    keys = list(zip(*(table[c] for c in qi)))
    groups = Counter(keys)
    k = min(groups.values())

    if flag:
        n = len(keys)
        groups_by_size = Counter(groups.values())

        bad_k = []
        for size in sorted(groups_by_size)[:5]:
            rows = size * groups_by_size[size]
            bad_k.append(f"K = {size}: {rows} строк ({rows / n * 100:.2f}%)")

        if k == 1:
            unique_rows = table[[groups[key] == 1 for key in keys]]
        else:
            unique_rows = table.iloc[0:0]

        return k, bad_k, unique_rows

    return k, None, None

def anonimise_date(value, level):
    if level == 1:
        return value[:10]
    if level == 2:
        return value[:7]
    if level == 3:
        quarter = (int(value[5:7]) - 1) // 3 + 1
        return f"{value[:4]}-Q{quarter}"
    if level == 4:
        return value[:4]
    if level >= 5:
        return "*"
    return value

PRICE_STEPS = {1: 5000, 2: 10000}

def anonimise_cost(value, level):
    if level == 0:
        return value
    if level >= 3:
        return "*"
    step = PRICE_STEPS[level]
    price = int(str(value).split()[0])
    bucket = (price - 1) // step
    return f"{bucket * step + 1}-{(bucket + 1) * step}"
    
def anonimise_sympthoms(value, level):
    if level == 0:
        return value
    if level >= 2:
        return "*"
    n = len(value.split(", "))
    if n < 4:
        return "1-3"
    if n < 8:
        return "4-7"
    return "8-10"

PROFILE_BY_SPECIALTY = {
    specialty: profile
    for profile, specialties in DOCTOR_PROFILES.items()
    for specialty in specialties
}

def anonimise_doctor(value, level):
    if level == 1:
        return PROFILE_BY_SPECIALTY.get(value, "other")
    if level >= 2:
        return "*"
    return value

@lru_cache(maxsize=None)
def research_category(name):
    return classify_research(name)

def anonimise_analyses(value, level):
    if level >= 3:
        return "*"
    if level == 0:
        return value

    categories = {research_category(a.strip()) for a in value.split(",")}

    if level == 1:
        return ", ".join(sorted(categories))
    return str(len(categories))

def anonymize(anon_df, qi, funcs, max_levels):
    n = len(anon_df)

    if n <= 51_000:
        needed_k = 10
    elif n <= 105_000:
        needed_k = 7
    else:
        needed_k = 5
    levels = {c: 0 for c in qi}
    full_anon_df = anon_df.copy()

    k, _, _ = k_anonimity(full_anon_df, qi)

    while k < needed_k:
        candidates = [c for c in qi if levels[c] < max_levels[c]]
        if not candidates:
            break

        col = max(candidates, key=lambda c: full_anon_df[c].nunique())
        levels[col] += 1
        level = levels[col]
        full_anon_df[col] = anon_df[col].map(lambda v: funcs[col](v, level))

        k, _, _ = k_anonimity(full_anon_df, qi)

    return full_anon_df, levels, k

funcs = {
    "Симптомы": anonimise_sympthoms,
    "Выбор врача": anonimise_doctor,
    "Дата посещения врача": anonimise_date,
    "Анализы": anonimise_analyses,
    "Дата получения анализов": anonimise_date,
    "Стоимость анализов": anonimise_cost,
}

max_levels = {
    "Симптомы": 2,
    "Выбор врача": 2,
    "Дата посещения врача": 5,
    "Анализы": 3,
    "Дата получения анализов": 5,
    "Стоимость анализов": 3,
}


def print_report(title, table, qi):
    k, bad_k, unique_rows = k_anonimity(table, qi, True)
    print(f"\n=== {title} ===")
    print(f"K = {k}")
    print("Худшие значения K:")
    for line in bad_k:
        print("  ", line)
    print(f"Уникальных строк (K = 1): {len(unique_rows)}")
    if len(unique_rows) > 0:
        print(unique_rows.head(10).to_string(index=False, max_colwidth=25))
        if len(unique_rows) > 10:
            print(f"... и ещё {len(unique_rows) - 10}")

print_report("До обобщения", anon_df, qi)

result_df, levels, k = anonymize(anon_df, qi, funcs, max_levels)

print("\nИтоговые уровни:", levels)
print_report("После обобщения", result_df, qi)

result_df.to_excel("dataset_anonymized.xlsx", index=False)

def column_kld(original, generalized):
    n = len(original)
    pair = pd.DataFrame({"orig": original.values, "gen": generalized.values})

    p = pair["orig"].value_counts() / n
    class_share = pair["gen"].value_counts() / n
    class_size = pair.groupby("gen")["orig"].nunique()
    gen_of = pair.drop_duplicates("orig").set_index("orig")["gen"].loc[p.index]

    q = class_share.loc[gen_of].values / class_size.loc[gen_of].values
    return float(np.sum(p.values * np.log2(p.values / q)))


def utility_loss(original_df, generalized_df, qi):
    per_column = {c: column_kld(original_df[c], generalized_df[c]) for c in qi}
    return per_column, sum(per_column.values())

per_column, total = utility_loss(anon_df, result_df, qi)

print("\n=== Потеря полезности (KLD, бит) ===")
for col, value in per_column.items():
    print(f"{col}: {value:.4f}")
print(f"Сумма: {total:.4f}")