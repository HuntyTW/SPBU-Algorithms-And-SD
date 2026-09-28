from dataclasses import dataclass, field
import random
import data
from datetime import datetime, timedelta, timezone
import pandas as pd

class Settings:
    
    VISITS_PER_CLIENT_DISTRIBUTION = {
    1: 0.45,   
    2: 0.25,
    3: 0.15,
    4: 0.08,
    5: 0.05,
    6: 0.02,
    }
    
    BANKS = {
    "Сбербанк":    {"weight": 0.2, "systems": {"МИР": 0.6, "Visa": 0.2, "Mastercard": 0.2}},
    "ВТБ":         {"weight": 0.2, "systems": {"МИР": 0.5, "Visa": 0.25, "Mastercard": 0.25}},
    "Тинькофф":    {"weight": 0.2, "systems": {"МИР": 0.4, "Visa": 0.2, "Mastercard": 0.4}},
    "Альфабанк":   {"weight": 0.2, "systems": {"МИР": 0.8, "Visa": 0.1, "Mastercard": 0.1}},
    "Газпромбанк": {"weight": 0.2, "systems": {"МИР": 0.9, "Visa": 0.05, "Mastercard": 0.05}},
    }
    
    BINS = {
    "Сбербанк":    {"МИР": "2202 20", "Visa": "4276 31", "Mastercard": "5469 38"},
    "ВТБ":         {"МИР": "2200 15", "Visa": "4272 29", "Mastercard": "5278 83"},
    "Тинькофф":    {"МИР": "2201 16", "Visa": "4377 73", "Mastercard": "5536 91"},
    "Альфабанк":   {"МИР": "2200 02", "Visa": "4289 06", "Mastercard": "5215 88"},
    "Газпромбанк": {"МИР": "2200 38", "Visa": "4248 58", "Mastercard": "5262 33"},
    }
    
    TARGET_ROWS = 50_000
    
    MSK = timezone(timedelta(hours=3))
    
    DATASET_START = datetime(2020, 1, 1, tzinfo=MSK)
    DATASET_END = datetime(2023, 12, 31, tzinfo=MSK)
    FIRST_VISIT_END = DATASET_END - timedelta(days=365)
    
    WORKING_HOURS_START = 8
    WORKING_HOURS_END = 18
    WORKING_DAYS = [0, 1, 2, 3, 4]
    
    ANALYSIS_PRICES = [500, 750, 1000, 1200, 1500, 1800, 2500, 3000, 4500, 6000]
    
    MAX_CARD_USES = 5
    
    CARD_REUSE_PROBABILITY = 0.7
    
    NEXT_VISIT_MAX_GAP_DAYS = 60

@dataclass
class Client:
    client_id: int
    fio: str
    gender: str
    passport: str
    snils: str
    planned_visits: int
    cards: dict = field(default_factory=dict)
    visits: list = field(default_factory=list)

def generate_passport():
    nation = random.choice(["RU", "BEL", "KZ"])
    if nation == "RU":
        series = "".join(str(random.randint(0,9)) for _ in range(4))
        number = "".join(str(random.randint(0,9)) for _ in range(6))
        return f"{series} {number}"
    if nation == "BEL":
        letter1 = random.choice("ABCDEFGHKM")
        digits = "".join(str(random.randint(0,9)) for _ in range(7))
        letter2 = random.choice("ABCDEFGHKM")
        return f"{letter1}{digits}{letter2}"
    if nation == "KZ":
        digits = "".join(str(random.randint(0,9)) for _ in range(9))
        return f"N{digits}"
    
def generate_fio_and_gender():
    gender = random.choice(["M", "F"])
    if gender == "M":
        name = random.choice(data.male_first_names)
        surname = random.choice(data.male_surnames)
        patronymic = random.choice(data.male_patronymics)
    else:
        name = random.choice(data.female_first_names)
        surname = random.choice(data.female_surnames)
        patronymic = random.choice(data.female_patronymics)
    
    fio = f"{surname} {name} {patronymic}"
    return fio, gender

def generate_snils():
    digits = "".join(str(random.randint(0, 9)) for _ in range(9))
    return f"{digits[0:3]}-{digits[3:6]}-{digits[6:9]} {random.randint(10, 99)}"

used_passports = set()
used_snils = set()

def generate_unique(generator, used):
    while True:
        value = generator()
        if value not in used:
            used.add(value)
            return value

def generate_client(client_id):

    fio, gender = generate_fio_and_gender()
    
    return Client(
        client_id = client_id,
        fio = fio,
        gender = gender,
        passport = generate_unique(generate_passport, used_passports),
        snils = generate_unique(generate_snils, used_snils),
        planned_visits = random.choices(
            list(Settings.VISITS_PER_CLIENT_DISTRIBUTION.keys()),
            list(Settings.VISITS_PER_CLIENT_DISTRIBUTION.values()))[0],
        cards = {},
        visits = []
    )
    
avg_visits = sum(k * v for k, v in Settings.VISITS_PER_CLIENT_DISTRIBUTION.items())
num_clients = round(Settings.TARGET_ROWS / avg_visits)
clients = [generate_client(i) for i in range(num_clients)]

active_clients = clients.copy()

@dataclass
class Visit:
    visit_id: int
    doctor: str
    symptoms: str
    date_visit: datetime
    card: str
    analyses: str
    date_analyses: datetime
    analyses_cost: int

@dataclass
class CardInfo:
    number: str
    bank: str
    system: str
    uses: int = 0
    
def generate_card():
    bank = random.choices(
        list(Settings.BANKS.keys()),
        [b["weight"] for b in Settings.BANKS.values()])[0]
    systems = Settings.BANKS[bank]["systems"]
    system = random.choices(
        list(systems.keys()),
        list(systems.values()))[0]
    bin_prefix = Settings.BINS[bank][system]
    return CardInfo(
            number = f"{bin_prefix}{random.randint(0, 99):02d} {random.randint(0, 9999):04d} {random.randint(0, 9999):04d}",
            bank = bank,
            system = system,
            uses=1
    )

def get_or_create_card(client):
    usable = [c for c in client.cards.values() if c.uses < Settings.MAX_CARD_USES]

    if usable and random.random() < Settings.CARD_REUSE_PROBABILITY:
        card = random.choice(usable)
        card.uses += 1         
    else:
        card = generate_card()  
        client.cards[card.number] = card

    return card

def random_visit_datetime():
    total_days = (Settings.FIRST_VISIT_END - Settings.DATASET_START).days
    while True:
        day = Settings.DATASET_START + timedelta(days=random.randint(0, total_days))
        if day.weekday() in Settings.WORKING_DAYS:
            break
    hour = random.randint(Settings.WORKING_HOURS_START, Settings.WORKING_HOURS_END - 1)
    minute = random.choice([0, 15, 30, 45])
    return day.replace(hour=hour, minute=minute)

def generate_analysis_date(date_visit: datetime):
    day = date_visit + timedelta(days=1)
    over_weekend = False
    while day.weekday() not in Settings.WORKING_DAYS:
        day += timedelta(days=1)
        over_weekend = True

    if over_weekend:
        hour = random.randint(Settings.WORKING_HOURS_START, date_visit.hour)
    else:
        hour = random.randint(date_visit.hour, Settings.WORKING_HOURS_END - 1)
    return day.replace(hour=hour)

def generate_next_visit_date(last_analysis_date: datetime):
    day = last_analysis_date + timedelta(days=random.randint(2, Settings.NEXT_VISIT_MAX_GAP_DAYS))
    while day.weekday() not in Settings.WORKING_DAYS:
        day += timedelta(days=1)
    hour = random.randint(Settings.WORKING_HOURS_START, Settings.WORKING_HOURS_END - 1)
    minute = random.choice([0, 15, 30, 45])
    return day.replace(hour=hour, minute=minute)

def generate_visit(visit_id):
    
    while True:
        if len(active_clients) == 0:
                client = generate_client(len(clients))
                clients.append(client)
                active_clients.append(client)
 
        idx = random.randrange(len(active_clients))
        client = active_clients[idx]
        
        if len(client.visits) >= client.planned_visits:
            active_clients[idx] = active_clients[-1]
            active_clients.pop()
        else:
            break
        
    DOCTORS_BY_GENDER = {
    g: [d for d in data.DOCTORS_DATA if d.get("gender", g) == g]
    for g in ("M", "F")
    }
    
    doctor_entry = random.choice(DOCTORS_BY_GENDER[client.gender])
    
    if client.visits:
        date_visit = generate_next_visit_date(client.visits[-1].date_analyses)
    else:
        date_visit = random_visit_datetime()

    visit = Visit(
        visit_id = visit_id,
        doctor = doctor_entry["specialty"],
        symptoms = ", ".join(random.sample(doctor_entry["symptoms"], k = random.randint(1, 10))),
        date_visit = date_visit,
        card = get_or_create_card(client).number,
        analyses = ", ".join(random.sample(doctor_entry["analyses"], k = random.randint(1, min(5, len(doctor_entry["analyses"]))))),
        date_analyses = generate_analysis_date(date_visit),
        analyses_cost = random.choice(Settings.ANALYSIS_PRICES)
    )
    client.visits.append(visit)
    return visit
        
visits = [generate_visit(i) for i in range(Settings.TARGET_ROWS)]

def build_rows():
    pairs = [(c, v) for c in clients for v in c.visits]
    pairs.sort(key=lambda p: p[1].date_visit)   

    rows = []
    for c, v in pairs:
        rows.append({
            "ФИО": c.fio,
            "Паспортные данные": c.passport,
            "СНИЛС": c.snils,
            "Симптомы": v.symptoms,
            "Выбор врача": v.doctor,
            "Дата посещения врача": v.date_visit.isoformat(timespec="minutes"),
            "Анализы": v.analyses,
            "Дата получения анализов": v.date_analyses.isoformat(timespec="minutes"),
            "Стоимость анализов": f"{v.analyses_cost} руб.",
            "Карта оплаты": v.card,
        })
    return rows

df = pd.DataFrame(build_rows())
df.to_excel("dataset.xlsx", index=False)