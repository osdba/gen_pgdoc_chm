#!/usr/bin/env python
# _*_ coding:UTF-8


import BeautifulSoup
import os
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
import glob

import codecs
import chardet
from optparse import OptionParser


def convert_html_encoding():
    file_list = glob.glob('htmlorigin/*.html')
    for fn in file_list:
        dstfn = 'html/%s' % os.path.basename(fn)
        # convert file from the source encoding to target encoding
        content = codecs.open(fn, 'r').read()
        src_encoding = chardet.detect(content)['encoding']
        # print src_encoding, fn
        if src_encoding is None:
            src_encoding = 'gbk'
        try:
            content = codecs.open(fn, "r", src_encoding).read()
            content = content.replace('charset=utf-8', 'charset=gbk')
        except UnicodeDecodeError:
            src_encoding = 'utf-8'
            try:
                content = codecs.open(fn, 'r', 'utf-8').read()
                content = content.replace('charset=gbk', 'charset=utf-8')
            except UnicodeDecodeError:
                print "Error: %s" % fn
                continue
        # content = content.decode(srcEncoding)
        try:
            codecs.open(dstfn, 'w', encoding='gbk').write(content)
        except UnicodeEncodeError:
            codecs.open(dstfn, 'w', encoding=src_encoding).write(content)


def gen_hhc(hhc_file):
    print "Begin generate %s " % hhc_file,
    head = '''<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
    <HTML>
    <HEAD>
    <meta name="GENERATOR" content="Microsoft&reg; HTML Help Workshop 4.1">
    <!-- Sitemap 1.0 -->
    </HEAD><BODY>
    '''
    fp = open(hhc_file, "w")

    fp.writelines(head)
    # print head
    toc_file = 'html/index.html'
    gen_hhc_body(fp, toc_file, 0)

    tail = '''
    </BODY></HTML>
    '''
    # print tail
    fp.writelines(tail)
    print "Generate %s finished."


def gen_hhc_body(fp, toc_file, level):
    if level > 0 and toc_file == 'html/index.html':
        return

    f = open(toc_file)
    web_data = f.read()
    f.close()
    soup = BeautifulSoup.BeautifulSoup(web_data)
    toc_list = soup.findAll('div', {"class": "TOC"})
    if toc_list is None or len(toc_list) <= 0:
        return
    toc = toc_list[0]
    if not hasattr(toc, 'contents'):
        return
    if len(toc.contents) <= 0:
        return

    if not hasattr(toc.contents[0], 'contents'):
        return

    level_space = level * ' '
    fp.writelines("%s<UL>\n" % level_space)

    dt_list = toc.contents[0].contents
    for dt in dt_list:
        if dt.a is None:
            continue

        if dt.dl is None:
            url = dt.a.get('href')
            title = dt.a.text

            s = '%s<LI> <OBJECT type="text/sitemap">' \
                '<param name="Name" value="%s">' \
                '<param name="Local" value="html\\%s">' \
                '</OBJECT>' \
                '</LI>\n' % (level_space, title, url)
            # print s.encode('gb2312')
            fp.writelines(level_space + s.encode('gbk'))

            # print "Process: %s%s %s" % (level_space, title, url)
            sys.stdout.write(".")
            sys.stdout.flush()
            if '#' in url:
                continue
            gen_hhc_body(fp, "html/%s" % url, level + 1)

    fp.writelines("%s</UL>\n" % level_space)


def gen_hhk(hhk_file, gbk):
    print "Begin generate %s ..." % hhk_file

    head = '''<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<HTML>
<HEAD>
<meta name="GENERATOR" content="Microsoft&reg; HTML Help Workshop 4.1">
<!-- Sitemap 1.0 -->
</HEAD><BODY>
<UL>
    '''
    hhk_fp = open(hhk_file, "w")

    hhk_fp.writelines(head)
    # print head

    file_list = glob.glob('html/*.html')
    for fn in file_list:

        f = open(fn)
        web_data = f.read()
        f.close()
        soup = BeautifulSoup.BeautifulSoup(web_data)
        # 如果html文档中没有title，则用文件名作索引项
        if not soup.title:
            title_text = os.path.splitext(os.path.basename(fn))[0]
            print "===== WARN: %s no soup.title" % fn
        else:
            title_text = soup.title.text

        s = '<LI> <OBJECT type="text/sitemap">' \
            '<param name="Name" value="%s">' \
            '<param name="Local" value="%s">' \
            '</OBJECT>\n' % (title_text, fn)
        if gbk:
            try:
                dest_s = s.encode('gb2312')
            except UnicodeEncodeError:
                print "Warn: convert file(%s) encoding to gbk failed: %s" % (fn, s)
                dest_s = s
        else:
            dest_s = s
        hhk_fp.writelines(dest_s)
    tail = '''
</UL>
</BODY></HTML>
    '''
    # print tail
    hhk_fp.writelines(tail)
    print "Finished."


def main():
    parser = OptionParser()

    parser.add_option("-n", "--name", action="store", dest="name", default="",
                      help="Specifies Chm name, not including the path and extension, example 'PostgreSQL9.4.5'")

    parser.add_option("-g", "--gbk", action="store_true", dest="gbk", default="",
                      help="Whether transcoding into GBK, if there Chinese content in html file, "
                           "you need to specify this parameter")

    (options, args) = parser.parse_args()

    if not options.name:
        print "You must specify the -n parameter"
        sys.exit(1)

    if options.gbk:
        convert_html_encoding()

    gen_hhc('%s.hhc' % options.name)
    gen_hhk('%s.hhk' % options.name, options.gbk)


if __name__ == "__main__":
    main()
