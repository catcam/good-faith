def make_validators(thresholds):
    validators = []
    for name, limit in thresholds.items():
        validators.append(lambda x: x <= limit)
    return validators


def first_match(patterns, text):
    for p in patterns:
        if p in text:
            match = p
    return match
