def convertGradeToPercentage(grade):
    if 1.0 <= grade <= 1.05:
        return 100
    elif 1.06 <= grade <= 1.11:
        return 99
    elif 1.12 <= grade <= 1.17:
        return 98
    elif 1.18 <= grade <= 1.24:
        return 97
    elif 1.25 <= grade <= 1.32:
        return 96
    elif 1.33 <= grade <= 1.4:
        return 95
    elif 1.41 <= grade <= 1.5:
        return 94
    elif 1.51 <= grade <= 1.57:
        return 93
    elif 1.58 <= grade <= 1.65:
        return 92
    elif 1.66 <= grade <= 1.74:
        return 91
    elif 1.75 <= grade <= 1.82:
        return 90
    elif 1.83 <= grade <= 1.9:
        return 89
    elif 1.91 <= grade <= 1.99:
        return 88
    elif 2.0 <= grade <= 2.07:
        return 87
    elif 2.08 <= grade <= 2.15:
        return 86
    elif 2.16 <= grade <= 2.24:
        return 85
    elif 2.25 <= grade <= 2.32:
        return 84
    elif 2.33 <= grade <= 2.4:
        return 83
    elif 2.41 <= grade <= 2.49:
        return 82
    elif 2.5 <= grade <= 2.57:
        return 81
    elif 2.58 <= grade <= 2.65:
        return 80
    elif 2.66 <= grade <= 2.74:
        return 79
    elif 2.75 <= grade <= 2.82:
        return 78
    elif 2.83 <= grade <= 2.9:
        return 77
    elif 2.91 <= grade <= 3.99:
        return 76
    elif 3.0 <= grade <= 3.1:
        return 75
    else:
        return 0  # Indicates an invalid grade


def checkStatus(grade):
    if grade <= 3.00 and grade >= 1.00:
        return "P"
    elif grade <= 4.00:
        return "Inc."
    else:
        return "D"
