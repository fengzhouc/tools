# encoding=utf-8
import time

from cmdline import parse_args


def ded():
    urls = []
    ded_urls = []
    args = parse_args()
    f = args.f
    # f = "domain.txt"
    if f.endswith("txt"):
        with open(f, encoding="utf-8") as file:
                for url in file:
                    for u in url.split(","):
                        if u != "" and u.strip() not in urls:
                            urls.append(u.strip())
                        else:
                            if u != "":
                                ded_urls.append(u.strip())
        with open("{}-{}.txt".format(f, time.time()), mode="w") as fie:
            urls.sort()
            for u in urls:
                fie.write("{}\n".format(u.strip()))
    print("##ded data:")
    ded_urls.sort()
    for url in list(set(ded_urls)):
        print(url.strip())
    # with open("{}-new.txt".format(f), mode="w", newline="\n") as fie:
    #     for url in list(set(urls)):
    #         fie.write("{}\n".format(url))


if __name__ == '__main__':
    ded()
