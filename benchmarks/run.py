import json
import random
import string
from datetime import datetime
from functools import partial
from pathlib import Path
from statistics import mean, stdev

from test_trafaret import TestTrafaret
from test_pydantic import TestPydantic
from test_drf import TestDRF

PUNCTUATION = ' \t\n!"#$%&\'()*+,-./'
LETTERS = string.ascii_letters
UNICODE = '\xa0\xad¡¢£¤¥¦§¨©ª«¬ ®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ'
ALL = PUNCTUATION * 5 + LETTERS * 20 + UNICODE
random = random.SystemRandom()


class GenerateData:
    def __init__(self):
        pass


def rand_string(min_length, max_length, corpus=ALL):
    return ''.join(random.choices(corpus, k=random.randrange(min_length, max_length)))


MISSING = object()


def null_missing_v(f, null_chance=0.2, missing_chance=None):
    r = random.random()
    if random.random() < null_chance:
        return None
    missing_chance = null_chance if missing_chance is None else missing_chance
    if r < (null_chance + missing_chance):
        return MISSING
    return f()


def null_missing_string(*args, **kwargs):
    f = partial(rand_string, *args)
    return null_missing_v(f, **kwargs)


def rand_email():
    if random.random() < 0.2:
        c1, c2 = UNICODE, LETTERS
    else:
        c1, c2 = LETTERS, LETTERS
    return f'{rand_string(10, 50, corpus=c1)}@{rand_string(10, 50, corpus=c2)}.{rand_string(2, 5, corpus=c2)}'


def null_missing_email():
    return null_missing_v(rand_email)


def rand_date():
    r = random.randrange
    return f'{r(1900, 2020)}-{r(0, 12)}-{r(0, 32)}T{r(0, 24)}:{r(0, 60)}:{r(0, 60)}'


def remove_missing(d):
    if isinstance(d, dict):
        return {k: remove_missing(v) for k, v in d.items() if v is not MISSING}
    elif isinstance(d, list):
        return [remove_missing(d_) for d_ in d]
    else:
        return d


def generate_case():
    return remove_missing(dict(
        id=random.randrange(1, 2000),
        client_name=null_missing_string(10, 280, null_chance=0.05, missing_chance=0.05),
        sort_index=random.random() * 200,
        client_email=null_missing_email(),  # email checks differ with different frameworks
        client_phone=null_missing_string(5, 15),
        location=dict(
            latitude=random.random() * 180 - 90,
            longitude=random.random() * 180,
        ),
        contractor=str(random.randrange(50, 2000)),
        upstream_http_referrer=null_missing_string(10, 1050),
        grecaptcha_response=null_missing_string(10, 1050, null_chance=0.05, missing_chance=0.05),
        last_updated=rand_date(),
        skills=[dict(
            subject=null_missing_string(5, 20, null_chance=0.01, missing_chance=0),
            subject_id=i,
            category=rand_string(5, 20),
            qual_level=rand_string(5, 20),
            qual_level_id=random.randrange(2000),
            qual_level_ranking=random.random() * 20
        ) for i in range(random.randrange(1, 5))]
    ))

THIS_DIR = Path(__file__).parent.resolve()


def main():
    json_path = THIS_DIR / 'cases.json'
    if not json_path.exists():
        print('generating test cases...')
        cases = [generate_case() for _ in range(2000)]
        with json_path.open('w') as f:
            json.dump(cases, f, indent=2, sort_keys=True)
    else:
        with json_path.open() as f:
            cases = json.load(f)
    tests = [TestTrafaret, TestDRF, TestPydantic]
    for test_class in tests:
        times = []
        p = test_class.package
        for i in range(5):
            count, pass_count = 0, 0
            start = datetime.now()
            test = test_class(False)
            for i in range(3):
                for case in cases:
                    passed, result = test.validate(case)
                    count += 1
                    pass_count += passed
            time = (datetime.now() - start).total_seconds()
            success = pass_count / count * 100
            print(f'{p:10} time={time:0.3f}s, success={success:0.2f}%')
            times.append(time)
        print(f'{p:10} best={min(times):0.3f}s, avg={mean(times):0.3f}s, stdev={stdev(times):0.3f}s')


if __name__ == '__main__':
    main()
