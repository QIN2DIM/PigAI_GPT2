import random
import string
from config import PATH_FAKE_CORPUS, TEXT_LENGTH


def load_fake_data(fp):
    source = []
    with open(fp, "r", encoding="utf-8") as f:
        data = [i.split(".", 1)[-1].strip() for i in f.read().split("\n") if "." in i]
    for i in data:
        src = i.split(".")
        for j in src:
            source.append(j.strip())

    random.shuffle(source)

    return source


def generate_fake_text(fp: str = PATH_FAKE_CORPUS):
    source = load_fake_data(fp)
    sample = ""
    while True:
        target = source.pop()
        try:
            if target[0] not in string.ascii_uppercase:
                continue
        except IndexError:
            continue
        sample += ".".join([target for i in range(1)]) + "."
        sample: str = sample[:-1] if sample.endswith("..") else sample
        # sample = sample[1:] if sample.startswith('.') else sample
        # print('\r{}'.format(sample.split(' ').__len__(), sample), end='')
        if sample.split(" ").__len__() > TEXT_LENGTH:
            return {"len": sample.split(" ").__len__(), "text": sample}
