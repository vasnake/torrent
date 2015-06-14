#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

# Copyright (c) Valentin Fedulov <vasnake@gmail.com>
# See COPYING for details.
#
# Find files on disk that not mentioned in torrent files.
# Torrent parser copied from
# * http://effbot.org/zone/bencode.htm
# * http://stackoverflow.com/questions/406695/reading-the-fileset-from-a-torrent

import os
import re

torrFolder = u'/mnt/rover/.config/deluge/state'
dataFolder = u'/mnt/rover/torrent/data'
FS_CP = 'utf-8'
TORR_CP = 'utf-8'

def findFiles(scandir, ext=u''):
    '''Returns list of file names with extension 'ext'
    recursively finded inside 'scandir'.
    If no ext provided, all files will be collected.

    scandir, ext is a unicode strings
    '''
    lstFiles = []
    for root, dirs, files in os.walk(scandir):
        for f in files:
            fn = os.path.join(root, f)
            if (ext and fn.endswith(u'.' + ext)) or not ext:
                lstFiles.append(unicode(fn))
            else: print u"extra file: '%s'" % fn
    return lstFiles


class TorrentInfo(object):
    """Information from torrent file.
    """

    def __init__(self, filename):
        self.data = open(filename, "rb").read()
        self.allinfo = self._decode(self.data)
        #self.printInfo()
        self.info = self.allinfo.get('info', {})

    def printInfo(self, info=''):
        """Print torrent information from info = decode(data)
        """
        if not info:
            info = self.allinfo

        for x in info: # dict keys
            if x == 'info':
                for y in info[x]:
                    if y == 'pieces':
                        continue
                    print "Torrent info: %s:%s" % (y, info[x][y])
            else:
                print "Torrent other: %s:%s" % (x, info[x])

    def getFilesList(self):
        dataFiles = []
        cp = TORR_CP

        name = self.getTorrName()
        if not name:
            self.printInfo()
            raise ValueError("Name is empty")

        files = self.info.get('files', [])
        #print "Name '%s', files '%s'" % (name, files)
        for f in files:
            path = self._filePath(f)
            fn = os.path.join(name, *path)
            dataFiles.append(fn.decode(cp))
        if not files:
            dataFiles.append(name.decode(cp))

        return dataFiles

    def getTorrName(self, info=''):
        if not info:
            info = self.info

        name = info.get('name.utf-8', '')
        if not name:
            name = info.get('name', '')
        return name

    def _filePath(self, fileItem):
        """Returns list from torrent['info']['files'][idx]['path'].

        for fileItem in files:
            path = self._filePath(fileItem)
        """
        idx = 'path.utf-8'
        if not fileItem.get(idx, ''):
            idx = 'path'
        return fileItem[idx]

    def _decode(self, text):
        try:
            src = self._tokenize(text)
            data = self._decode_item(src.next, src.next())
            for token in src: # look for more tokens
                raise SyntaxError("trailing junk")
        except (AttributeError, ValueError, StopIteration):
            raise SyntaxError("syntax error")
        return data

    def _tokenize(self, text, match=re.compile("([idel])|(\d+):|(-?\d+)").match):
        i = 0
        while i < len(text):
            m = match(text, i)
            s = m.group(m.lastindex)
            i = m.end()
            if m.lastindex == 2:
                yield "s"
                yield text[i:i+int(s)]
                i = i + int(s)
            else:
                yield s

    def _decode_item(self, next, token):
        if token == "i":
            # integer: "i" value "e"
            data = int(next())
            if next() != "e":
                raise ValueError
        elif token == "s":
            # string: "s" value (virtual tokens)
            data = next()
        elif token == "l" or token == "d":
            # container: "l" (or "d") values "e"
            data = []
            tok = next()
            while tok != "e":
                data.append(self._decode_item(next, tok))
                tok = next()
            if token == "d":
                data = dict(zip(data[0::2], data[1::2]))
        else:
            raise ValueError
        return data


def getDataFilesFromTorrent(torrent):
    """Returns list of names for torrent data files.
    Names are unicode strings.
    """
    ti = TorrentInfo(torrent)
    dataFiles = ti.getFilesList()
    return dataFiles


def main():
    """Find all torrent files in folder;
    parse each torrent and find datafile names;
    find all datafiles in data folder;
    compare two lists and find datafiles not in torrents.
    """
    print (
        "Torrent files folder: '%s'; "
        "data files folder: '%s'") % (torrFolder, dataFolder)
    allTorrDataFiles = []
    torrents = findFiles(torrFolder, u'torrent')
    for t in torrents:
        #print "Torrent: '%s'" % t
        dataFiles = getDataFilesFromTorrent(t)
        #print u"Torrent data files: %s" % u'\n\t'.join(sorted(dataFiles))
        allTorrDataFiles += dataFiles

    allTorrDataFiles = [
        os.path.join(dataFolder, x) for x in allTorrDataFiles
    ]
    print u"Torrent file sample: %s" % allTorrDataFiles[0]
    print "Number ot torrents data files: %s" % len(allTorrDataFiles)

    filesOnDisk = findFiles(dataFolder)
    print u"Disk file sample: %s" % filesOnDisk[0]
    print "Number ot disk data files: %s" % len(filesOnDisk)

    torrSet = frozenset(allTorrDataFiles)
    fileSet = frozenset(filesOnDisk)
    diff = fileSet - torrSet
    print u"Extra files: %s" % u'\n\t'.join(sorted(diff))
    diff = torrSet - fileSet
    print u"Files to download: %s" % u'\n\t'.join(sorted(diff))


if __name__ == '__main__':
    main()
