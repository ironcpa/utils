# -*- coding: utf-8 -*-

import os

def rename_files(path):
    #remove_str = "[Thz.la]"
    remove_strs = ["[Thz.la]",
                   "[thz.la]",
                   "21bt.net-"
                   "1203-javbo.net_",
                   "0814",
                   "1018",
                   "1019",
                   "1020",
                   ]
    for root, dirs, files in os.walk(path):
        for f in files:
            os.chdir(root)

            print('file',f)
            for rs in remove_strs:
                if f.find(rs) >= 0:
                    new_name = f.replace(rs, "")
                    print(new_name, "<-", f)
                    os.rename(f, new_name)

rename_files("D:/새 폴더")
