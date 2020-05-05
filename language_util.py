from iso639 import languages as iso_languages

def add_languages(languages, srcs, tgts):
    """Add language directions to a dictionary"""

    for sl in srcs.split():
        for tl in tgts.split():
            if sl != tl:
                if sl not in languages:
                    languages[sl] = [tl]
                else:
                    languages[sl].append(tl)
    return languages

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

    languages = {}
    units = langstr.split(', ')

    for unit in units:
        if '<->' in unit:
            srcs, tgts = unit.split('<->')
            languages = add_languages(languages, srcs, tgts)
            languages = add_languages(languages, tgts, srcs)
        elif '->' in unit:
            srcs, tgts = unit.split('->')
            languages = add_languages(languages, srcs, tgts)
        elif '(' in unit and ')' in unit:
            unit = unit[1:-1]
            languages = add_languages(languages, unit, unit)

    source_langs = {}
    target_langs = []

    for key in languages.keys():
        lan_name = get_lang_name(key)
        if lan_name:
            source_langs[(lan_name, key)] = languages[key]
            for tgt_lan in languages[key]:
                if tgt_lan not in target_langs:
                    target_langs.append(tgt_lan)

    target_langs = create_language_list(target_langs)

    return source_langs, target_langs
