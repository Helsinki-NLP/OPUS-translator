import html

def formHighlightString(sent, orig_seg, tag_seg, raw=False):
    """Make final segmented string."""
    if raw:
        i = 0
        repl = ''
        ret = '<span class="word">'
        for c in sent:
            if c == ' ':
                ret += repl+'</span> <span class="word">'
            else:
                repl += c
                if (repl == orig_seg[i].replace('@@', '') or
                        '@{}@'.format(repl) == orig_seg[i]):
                    if repl in ['.', ',', '!', '?']:
                        ret += '</span><span class="word">'
                    ret += tag_seg[i].replace('@@', '').replace('@-@', '-')
                    i += 1
                    repl = ''
        return ret+'</span> '
    else:
        ret = '<span class="word">'
        for tag in tag_seg:
            if '@@' in tag:
                ret += tag.replace('@@', '')
            else:
                ret += tag+'</span> <span class="word">'
        return ret+'</span> '

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

def highlight_one(source, target, source_seg, target_seg, alignment, si, raw=False):
    """Return source and target sentences with alignment segments."""
    alignment = alignment.split()
    source_seg_orig = source_seg
    target_seg_orig = target_seg
    source_seg = html.unescape(source_seg).split()# + ['EOS']
    target_seg = html.unescape(target_seg).split()# + ['EOS']
    source_seg_new = [[set(), i] for i in source_seg]
    target_seg_new = [[set(), i] for i in target_seg]
    all_segs = set()

    for alig in alignment:
        alig = alig.split('-')
        s, t = int(alig[0]), int(alig[1])
        #Skip EOS
        if s == len(source_seg) or t == len(target_seg):
            continue
        suffixes = ['-'+si+'-s'+str(s), '-'+si+'-t'+str(t)]
        source_seg_new[s][0].update(suffixes)
        source_seg_new[s][1] = source_seg[s]
        target_seg_new[t][0].update(suffixes)
        target_seg_new[t][1] = target_seg[t]
        all_segs.update(suffixes)

    source_seg_highlight = addSegs(source_seg_new)
    target_seg_highlight = addSegs(target_seg_new)

    source_res = formHighlightString(
        source, source_seg, source_seg_highlight, raw)
    target_res = formHighlightString(
        target, target_seg, target_seg_highlight, raw)

    return source_res, target_res, all_segs

def highlight(data, raw=False):
    source_res, target_res, all_segs = '', '', []
    si = 0
    if raw:
        source_sentences = data['source-sentences']
        target_sentences = data['target-sentences']
    else:
        source_sentences = ['' for i in range(len(data['alignment']))]
        target_sentences = ['' for i in range(len(data['alignment']))]
    for source, target, source_seg, target_seg, alignment in zip(source_sentences, target_sentences, data['source-segments'], data['target-segments'], data['alignment']):
        source_res_temp, target_res_temp, all_segs_temp = highlight_one(
            source, target, source_seg, target_seg, alignment, str(si), raw)
        source_res += source_res_temp
        target_res += target_res_temp
        all_segs += all_segs_temp
        si += 1
    return source_res, target_res, all_segs
