from iso639 import languages as iso_languages

def add_languages(src_langs, tgt_langs, srcs_str, tgts_str):
    """Add language directions lists"""

    for sl in srcs_str.split():
        for tl in tgts_str.split():
            if sl != tl:
                if sl not in src_langs:
                    src_langs.append(sl)
                    tgt_langs.append([tl])
                else:
                    tgt_langs[src_langs.index(sl)].append(tl)
    return src_langs, tgt_langs

def get_lang_name(lan):
    """Get language name from iso639 abbreviation"""

    try:
        if len(lan) == 2:
            lan_name = iso_languages.get(alpha2=lan).name
        elif len(lan) == 3:
            lan_name = iso_languages.get(part3=lan).name
        return lan_name
    except Exception as e:
        return None

def create_language_list(language_str):
    """Create language name and abbrv. tuple list from
    space separated string"""

    languages = []
    for lan in language_str:
        lan_name = get_lang_name(lan)
        if lan_name:
            languages.append((lan_name, lan))
    return languages

def get_lang_directions(langstr):
    """Get a dict of src languages with possible tgt languages and
    a list of tgt languages from a string such as
    'fr en<->ga cy wl, en->fi sv, (sv no da)'"""

    src_langs, tgt_langs = [], []
    units = langstr.split(', ')

    for unit in units:
        if '<->' in unit:
            srcs, tgts = unit.split('<->')
            languages = add_languages(src_langs, tgt_langs, srcs, tgts)
            languages = add_languages(src_langs, tgt_langs, tgts, srcs)
        elif '->' in unit:
            srcs, tgts = unit.split('->')
            languages = add_languages(src_langs, tgt_langs, srcs, tgts)
        elif '(' in unit and ')' in unit:
            unit = unit[1:-1]
            languages = add_languages(src_langs, tgt_langs, unit, unit)

    src_lang_names = []
    tgt_lang_names = []

    for sl in src_langs:
        lan_name = get_lang_name(sl)
        if lan_name:
            src_lang_names.append(
                (lan_name, sl, tgt_langs[src_langs.index(sl)]))
            for tgt_lan in tgt_langs[src_langs.index(sl)]:
                if tgt_lan not in tgt_lang_names:
                    tgt_lang_names.append(tgt_lan)

    tgt_lang_names = create_language_list(tgt_lang_names)

    return src_lang_names, tgt_lang_names
