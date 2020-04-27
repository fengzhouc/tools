# encoding=utf-8
from cmdline import parse_args


def ded():
    urls = []
    args = parse_args()
    f = args.f
    if f.endswith("txt"):
        with open(f, encoding="utf-8") as file:
            for url in file:
                urls.append(url.strip())
    with open("{}-new.txt".format(f), mode="w", newline="\n") as fie:
        for url in list(set(urls)):
            fie.write("{}\n".format(url))


if __name__ == '__main__':
    ded()
