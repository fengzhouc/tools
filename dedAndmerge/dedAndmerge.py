# encoding=utf-8
import time

from cmdline import parse_args


def ded_ip(f):
    urls = []
    ded_urls = []
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

def ded_line(f):
    urls = []
    ded_urls = []
    # f = "domain.txt"
    if f.endswith("txt"):
        with open(f, encoding="utf-8") as file:
            for url in file:
                if url != "" and url.strip() not in urls:
                    urls.append(url.strip())
                else:
                    if url != "":
                        ded_urls.append(url.strip())
        with open("{}-{}.txt".format(f, time.time()), mode="w") as fie:
            urls.sort()
            for u in urls:
                fie.write("{}\n".format(u.strip()))
    print("##ded data:")
    ded_urls.sort()
    for url in list(set(ded_urls)):
        print(url.strip())
    pass

def ded_fei(f,f1):
    urls = []
    ded_urls = []
    # f = "domain.txt"
    if f.endswith("txt"):
        with open(f, encoding="utf-8") as file:
            for url in file:
                if url != "" and url.strip() not in urls:
                    urls.append(url.strip())
        with open("{}-{}.txt".format(f, time.time()), mode="w") as fie:
            with open(f1, encoding="utf-8") as file:
                for line in file:
                    if line.strip() not in urls:
                        fie.write("{}\n".format(line.strip()))
    print("##ded data:")
    ded_urls.sort()
    for url in list(set(ded_urls)):
        print(url.strip())
    pass

if __name__ == '__main__':
    args = parse_args()
    f = args.f
    t = args.t
    if t == "line":
        ded_line(f)
    elif t == "ip":
        ded_ip(f)
    elif t == "fei":
        f1 = args.f1
        ded_fei(f, f1)
