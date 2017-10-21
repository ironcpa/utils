BRAND_LEN = 3


def make_valid_product_name(src_name):
    np = -1
    for i, c in enumerate(src_name):
        if i + 1 > BRAND_LEN and c.isdigit():
            np = i
            break
    # sp = [x.isdigit() for x in s].index(True)

    brand = src_name[0:np]
    number = src_name[np:]

    print(src_name, np, brand, number)

    return brand + '-' + number


def remove_date_prefix(src_name):
    if len(src_name) < 4:
        return

    if not src_name[:4].isdigit():
        return

    # check month
    has_date_prefix = False
    month = int(src_name[:2])
    day = int(src_name[2:4])
    if month <= 12 and day <= 31:
        has_date_prefix = True

    # call remove substring

    return ''


if __name__ == '__main__':
    valid_name = make_valid_product_name("aaa111")
    print(valid_name)