#!/usr/bin/env python
"""
Exports a list of all image files in a Lightroom catalog.
Known issues:
- Doesn't understand virtual copies (the original filename will be listed once
  for each virtual copy)
- Hard-coded to sort by capture time (see "ORDER BY" clause in
  'list_collection')
"""

import sys
from glob import glob
from optparse import OptionParser
from os import path
import sqlite3 as sqlite


def error(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(1)


def list_collections(cxn):
    query = """SELECT id_local, name, parent
               FROM AgLibraryCollection"""
    for (id, name, parent_id) in cxn.execute(query):
        yield (id, name, parent_id)


def list_collection(cxn, id_or_name):
    query = """SELECT rootfolder.absolutePath, folder.pathFromRoot, file.idx_filename
               FROM
                   Adobe_images img,
                   AgLibraryCollection collection,
                   AgLibraryCollectionImage collectionimg,
                   AgLibraryFile file,
                   AgLibraryFolder folder,
                   AgLibraryRootFolder rootfolder
               WHERE
                   (collection.name = ? OR collection.id_local = ?) AND
                   collectionimg.collection = collection.id_local AND
                   img.id_local = collectionimg.image AND
                   file.id_local = img.rootFile AND
                   folder.id_local = file.folder AND
                   folder.rootFolder = rootfolder.id_local
                ORDER BY img.captureTime"""
    for (rootpath, path, name) in cxn.execute(query, (id_or_name, id_or_name)):
        yield rootpath + path + name


def main():
    usage = ("Usage: %prog [-d DATABASE] [COLLECTION]\n" +
             "Lists all the images, in order of creation date, in a \n" +
             "Lightroom catalog.")
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--db", dest="database", metavar="DATABASE",
                      help="Path to Lightroom folder or database",
                      default=".")

    options, args = parser.parse_args()

    if path.isdir(options.database):
        lrcats = glob(options.database + "/*.lrcat")
        if not lrcats:
            error("no Lightroom database found at %r" %(options.database, ))
        if len(lrcats) > 1:
            error("multiple Lightroom databases found: %s"
                  %(", ".join(map(repr, lrcats)), ))
        database = lrcats[0]
    else:
        database = options.database

    cxn = sqlite.connect(database)

    if len(args) == 0:
        sys.stderr.write("no collection specified; available collections:\n")
        for id, collection, parent_id in list_collections(cxn):
            parent_str = ""
            if parent_id is not None:
                parent_str = " (child of %s)" %(parent_id, )
            sys.stderr.write("%8d: %s%s\n" %(id, collection, parent_str))
        sys.exit(1)

    for img_path in list_collection(cxn, args[0]):
        print(img_path)

    sys.exit(0)

if __name__ == "__main__":
    main()