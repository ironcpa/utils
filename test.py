











def get_all_lines(max_reel, max_row):
    row = [0, 1, 2]
    counter = 0
    for r0 in row:
        for r1 in row:
            for r2 in row:
                for r3 in row:
                    for r4 in row:
                        print('{}{}{}{}{}'.format(r0, r1, r2, r3, r4))
                        counter = counter + 1
    print('count={}'.format(counter))

#get_all_lines(5, 3)


row = [0, 1, 2]
collect = []
def loop(times, line):
    if times == 0:
        collect.append(line)
        print('if times={} len={}'.format(times, len(line)))
        print(' {}{}{}{}{}'.format(line[0], line[1], line[2], line[3], line[4]))
        #del line[:]
        return
    for e in row:
        line.append(e)
        print('for times={} e={} len={}'.format(times, e, len(line)))
        loop(times-1, line)

loop(5, [])

print('count={}'.format(len(collect)))

#for e in collect:
#    print('{}{}{}{}{}'.format(e[0], e[1], e[2], e[3], e[4]))

print('{}{}{}'.format(row[0], row[1], row[2]))
