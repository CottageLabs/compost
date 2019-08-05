import os, time
from compost.context import context

def watch(dir, callback, frequency=2):
    tree = {}

    while True:
        # first read the tree
        newtree = {}
        for dirpath, dirnames, filenames in os.walk(dir):
            if len(filenames) > 0:
                for f in filenames:
                    filepath = os.path.join(dirpath, f)
                    mod = os.stat(filepath).st_mtime
                    newtree[filepath] = mod

        report = {
            "new" : [],
            "removed" : [],
            "modified" : []
        }

        # now compare new tree to old tree
        for filepath, mod in newtree.items():
            if filepath not in tree:
                report["new"].append(filepath)
            else:
                if newtree[filepath] != tree[filepath]:
                    report["modified"].append(filepath)
        for filepath, mod in tree.items():
            if filepath not in newtree:
                report["removed"].append(filepath)

        tree = newtree

        if callback is not None:
            if len(report["new"]) > 0 or len(report["removed"]) > 0 or len(report["modified"]) > 0:
                callback(report)

        time.sleep(frequency)

