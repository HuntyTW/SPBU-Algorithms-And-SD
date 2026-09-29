from datetime import datetime, timedelta, timezone

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
    
    BASE_ANALYSIS_PRICE = 500          
    PRICE_PER_EXTRA_ITEM = (300, 800)  
    PRICE_NOISE = (-100, 150)         
    
    MAX_CARD_USES = 5
    
    CARD_REUSE_PROBABILITY = 0.7
    
    NEXT_VISIT_MAX_GAP_DAYS = 60