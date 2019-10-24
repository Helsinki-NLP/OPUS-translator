import html

def formHighlightString(sent, orig_seg, tag_seg):
    """Make final segmented string."""
    i = 0
    repl = ''
    ret = '<span class="word">'
    for c in sent:
        if c == ' ':
            ret += repl+'</span> <span class="word">'
        else:
            repl += c
            if repl == orig_seg[i].replace('@@', ''):
                ret += tag_seg[i].replace('@@', '')
                i += 1
                repl = ''
    return ret+'</span>'

def addSegs(seg):
    """Create segment tags."""
    seg_highlight = []
    for s in seg:
        tag = '<span class="'
        classes = ['seg{}'.format(i) for i in s[0]]
        tag += ' '.join(classes)
        tag += '">{}</span>'.format(s[1])
        seg_highlight.append(tag)
    return seg_highlight

def highlight(source, data):
    """Return source and target sentences with alignment segments."""
    result = data['result']
    alignment = data['alignment'][0].split()
    source_seg = html.unescape(data['source-segments'][0]).split() + ['EOS']
    target_seg = html.unescape(data['target-segments'][0]).split() + ['EOS']
    source_seg_new = [[set(), i] for i in source_seg]
    target_seg_new = [[set(), i] for i in target_seg]
    all_segs = set()

    for alig in alignment:
        alig = alig.split('-')
        s, t = int(alig[0]), int(alig[1])
        suffixes = ['-s'+str(s), '-t'+str(t)]
        source_seg_new[s][0].update(suffixes)
        source_seg_new[s][1] = source_seg[s]
        target_seg_new[t][0].update(suffixes)
        target_seg_new[t][1] = target_seg[t]
        all_segs.update(suffixes)

    source_seg_highlight = addSegs(source_seg_new)
    target_seg_highlight = addSegs(target_seg_new)

    source_res = formHighlightString(source, source_seg, source_seg_highlight)
    target_res = formHighlightString(result, target_seg, target_seg_highlight)

    return source_res, target_res, all_segs
