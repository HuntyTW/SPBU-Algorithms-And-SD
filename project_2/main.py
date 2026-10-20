import numpy as np
import pandas as pd
from collections import Counter
from functools import lru_cache
from data_group import DOCTOR_PROFILES, classify_research

print("Читаем датасет")

df = pd.read_excel("dataset.xlsx")

STAR_COLUMNS = ["Паспортные данные", "СНИЛС"]
SUPPRESSION_LIMIT = 0.05

QI_COLUMNS = [
    "ФИО",
    "Симптомы",
    "Выбор врача",
    "Дата посещения врача",
    "Анализы",
    "Дата получения анализов",
    "Стоимость анализов",
    "Карта оплаты",
]


def ask_quasi_identifiers():
    print("\nСтолбцы:")
    for i, col in enumerate(QI_COLUMNS, 1):
        print(f"{i}. {col}")
    while True:
        raw = input("Номера квази-идентификаторов через пробел: ").split()
        if raw and all(x.isdigit() and 1 <= int(x) <= len(QI_COLUMNS) for x in raw):
            return [QI_COLUMNS[n - 1] for n in sorted(set(map(int, raw)))]
        print(f"Нужно ввести хотя бы один номер от 1 до {len(QI_COLUMNS)}")


def get_needed_k(n):
    if n <= 51_000:
        return 10
    elif n <= 105_000:
        return 7
    else:
        return 5


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


def small_groups_share(table, qi, needed_k):
    groups = Counter(zip(*(table[c] for c in qi)))
    k = min(groups.values())
    bad_rows = sum(size for size in groups.values() if size < needed_k)
    return k, bad_rows / len(table)


def anonimise_fio(value, level):
    if level == 0:
        return value
    if level >= 2:
        return "*"
    patronymic = value.split()[-1]
    return "М" if patronymic.endswith("ич") else "Ж"


BINS = {
    "Сбербанк":    {"МИР": "2202 20", "Visa": "4276 31", "Mastercard": "5469 38"},
    "ВТБ":         {"МИР": "2200 15", "Visa": "4272 29", "Mastercard": "5278 83"},
    "Тинькофф":    {"МИР": "2201 16", "Visa": "4377 73", "Mastercard": "5536 91"},
    "Альфабанк":   {"МИР": "2200 02", "Visa": "4289 06", "Mastercard": "5215 88"},
    "Газпромбанк": {"МИР": "2200 38", "Visa": "4248 58", "Mastercard": "5262 33"},
}

CARD_BY_BIN = {
    bin_code.replace(" ", ""): (bank, system)
    for bank, systems in BINS.items()
    for system, bin_code in systems.items()
}


def anonimise_card(value, level):
    if level == 0:
        return value
    if level >= 3:
        return "*"
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    bank, system = CARD_BY_BIN.get(digits[:6], ("Другой банк", "Другая система"))
    if level == 1:
        return f"{bank}, {system}"
    return system


def anonimise_date(value, level):
    if level == 0:
        return value
    if level == 1:
        return value[:10]
    if level == 2:
        return value[:7]
    if level == 3:
        quarter = (int(value[5:7]) - 1) // 3 + 1
        return f"{value[:4]}-Q{quarter}"
    if level == 4:
        return value[:4]
    return "*"


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
    if level == 0:
        return value
    if level == 1:
        return PROFILE_BY_SPECIALTY.get(value, "other")
    return "*"


@lru_cache(maxsize=None)
def research_category(name):
    return classify_research(name)


def anonimise_analyses(value, level):
    if level == 0:
        return value
    if level >= 3:
        return "*"
    categories = {research_category(a.strip()) for a in value.split(",")}
    if level == 1:
        return ", ".join(sorted(categories))
    return str(len(categories))


funcs = {
    "ФИО": anonimise_fio,
    "Симптомы": anonimise_sympthoms,
    "Выбор врача": anonimise_doctor,
    "Дата посещения врача": anonimise_date,
    "Анализы": anonimise_analyses,
    "Дата получения анализов": anonimise_date,
    "Стоимость анализов": anonimise_cost,
    "Карта оплаты": anonimise_card,
}

max_levels = {
    "ФИО": 2,
    "Симптомы": 2,
    "Выбор врача": 2,
    "Дата посещения врача": 5,
    "Анализы": 3,
    "Дата получения анализов": 5,
    "Стоимость анализов": 3,
    "Карта оплаты": 3,
}


def generalize_column(source, col, level):
    return source[col].map(lambda v: funcs[col](v, level))


def remove_direct_identifiers(source):
    table = source.copy()
    for col in STAR_COLUMNS:
        table[col] = "*"
    return table


def suppress(table, qi, needed_k):
    keys = list(zip(*(table[c] for c in qi)))
    groups = Counter(keys)
    kept = table[[groups[key] >= needed_k for key in keys]]
    return kept, len(table) - len(kept)


def anonymize(source, base, qi, needed_k):
    levels = {c: 0 for c in qi}
    table = base.copy()

    k, share = small_groups_share(table, qi, needed_k)

    for reserve in (1, 0):
        while share > SUPPRESSION_LIMIT:
            candidates = [c for c in qi if levels[c] < max_levels[c] - reserve]
            if not candidates:
                break
            col = max(candidates, key=lambda c: table[c].nunique())
            levels[col] += 1
            table[col] = generalize_column(source, col, levels[col])
            k, share = small_groups_share(table, qi, needed_k)

    table, removed = suppress(table, qi, needed_k)
    return table, levels, removed


def print_report(title, table, qi):
    k, bad_k, unique_rows = k_anonimity(table, qi, True)
    print(f"\n=== {title} ===")
    print(f"K = {k}")
    print("Худшие значения K:")
    for line in bad_k:
        print("  ", line)
    print(f"Уникальных строк (K = 1): {len(unique_rows)}")
    if len(unique_rows) > 0:
        print(unique_rows[qi].head(10).to_string(index=False, max_colwidth=25))
        if len(unique_rows) > 10:
            print(f"... и ещё {len(unique_rows) - 10}")


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
    original_df = original_df.loc[generalized_df.index]
    per_column = {c: column_kld(original_df[c], generalized_df[c]) for c in qi}
    return per_column, sum(per_column.values())

print_report("Входной датасет", df, list(df.columns))

qi = ask_quasi_identifiers()

needed_k = get_needed_k(len(df))
print(f"\nДопустимое значение K для {len(df)} строк: K >= {needed_k}")

base_df = remove_direct_identifiers(df)
result_df, levels, removed = anonymize(df, base_df, qi, needed_k)

print("\nИтоговые уровни обобщения:", levels)
print(f"Удалено строк (локальное подавление): {removed} ({removed / len(df):.2%})")
print_report("Обезличенный датасет", result_df, qi)

per_column, total = utility_loss(df, result_df, list(df.columns))
print("\n=== Потеря полезности (KLD, бит) ===")
for col, value in per_column.items():
    print(f"{col}: {value:.4f}")
print(f"Сумма: {total:.4f}")

result_df.to_excel("dataset_anonymized.xlsx", index=False)