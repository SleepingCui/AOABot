MARGIN_MAP = {
    0: {"label": "TooEarly", "color": "#FF2A2A"},  
    1: {"label": "VeryEarly", "color": "#FF8C55"}, 
    2: {"label": "EarlyPerfect", "color": "#B8FF36"}, 
    3: {"label": "Perfect", "color": "#00FF66"},  
    4: {"label": "LatePerfect", "color": "#B8FF36"},  
    5: {"label": "VeryLate", "color": "#FF8C55"},  
    6: {"label": "TooLate", "color": "#FF2A2A"},  
    7: {"label": "Multipress", "color": "#00FFFF"},  
    8: {"label": "FailMiss", "color": "#E56BFF"},  
    9: {"label": "FailOverload", "color": "#E56BFF"},
    10: {"label": "Auto", "color": "#FFFFFF"}, 
    11: {"label": "OverPress", "color": "#E56BFF"},
    12: {"label": "XPerfect", "color": "#38E8FF"},  
}

DISPLAY_ORDER = [9, 0, 1, 2, 12, 3, 4, 5, 7, 8, 10]

JD_WEIGHTS = {
    "failMiss": 0.0,
    "tooEarly": 0.2,
    "early": 0.4,
    "ePerfect": 0.75,
    "perfect": 1.0,
    "xPerfect": 1.0,
    "auto": 1.0,
    "lPerfect": 0.75,
    "late": 0.4,
}
