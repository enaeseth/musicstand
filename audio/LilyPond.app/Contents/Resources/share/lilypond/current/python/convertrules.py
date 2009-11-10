# (setq py-indent-offset 4)


import string
import re
import sys
import lilylib

_ = lilylib._


NOT_SMART = _ ("Not smart enough to convert %s")
UPDATE_MANUALLY	= _ ("Please refer to the manual for details, and update manually.")
FROM_TO = _ ( "%s has been replaced by %s")


class FatalConversionError:
    pass

conversions = []
stderr_write = lilylib.stderr_write

def warning (str):
    stderr_write (_ ("warning: %s") % str)

# Decorator to make rule syntax simpler
def rule (version, message):
    """
    version: a LilyPond version tuple like (2, 11, 50)
    message: the message that describes the conversion.

    This decorator adds its function together with the version and the
    message to the global conversions list.  (It doesn't need to return
    the function as it isn't used directly anyway.)

    A conversion rule using this decorator looks like this:

    @rule ((1, 2, 3), "convert foo to bar")
    def conv(str):
        str = str.replace('foo', 'bar')
        return str

    """
    def dec(f):
        conversions.append ((version, f, message))
    return dec


@rule ((0, 1, 9), _ ('\\header { key = concat + with + operator }'))
def conv(str):
    if re.search ('\\\\multi', str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % "\\multi")
	stderr_write ('\n')
    return str


@rule ((0, 1, 19), _ ('deprecated %s') % '\\octave')
def conv (str):
    if re.search ('\\\\octave', str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % "\\octave")
	stderr_write ('\n')
	stderr_write (UPDATE_MANUALLY)
	stderr_write ('\n')
    #	raise FatalConversionError ()
    return str


@rule ((0, 1, 20), _ ('deprecated \\textstyle, new \\key syntax'))
def conv (str):
    str = re.sub ('\\\\textstyle([^;]+);',
			     '\\\\property Lyrics . textstyle = \\1', str)
    # harmful to current .lys
    # str = re.sub ('\\\\key([^;]+);', '\\\\accidentals \\1;', str)
    return str


@rule ((0, 1, 21), '\\musical_pitch -> \\musicalpitch, \\meter -> \\time')
def conv (str):
    str = re.sub ('\\\\musical_pitch', '\\\\musicalpitch',str)
    str = re.sub ('\\\\meter', '\\\\time',str)
    return str


@rule ((1, 0, 0), _ ("bump version for release"))
def conv (str):
    return str


@rule ((1, 0, 1), '\\accidentals -> \\keysignature, specialaccidentals -> keyoctaviation')
def conv (str):
    str = re.sub ('\\\\accidentals', '\\\\keysignature',str)
    str = re.sub ('specialaccidentals *= *1', 'keyoctaviation = 0',str)
    str = re.sub ('specialaccidentals *= *0', 'keyoctaviation = 1',str)
    return str


@rule ((1, 0, 2), _ ('\\header { key = concat + with + operator }'))
def conv(str):
    if re.search ('\\\\header', str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % _ ("new \\header format"))
	stderr_write ('\n')
    return str


@rule ((1, 0, 3), '\\melodic -> \\notes')
def conv(str):
    str =  re.sub ('\\\\melodic([^a-zA-Z])', '\\\\notes\\1',str)
    return str


@rule ((1, 0, 4), 'default_{paper,midi}')
def conv(str):
    str =  re.sub ('default_paper *=', '',str)
    str =  re.sub ('default_midi *=', '',str)
    return str


@rule ((1, 0, 5), 'ChoireStaff -> ChoirStaff')
def conv(str):
    str =  re.sub ('ChoireStaff', 'ChoirStaff',str)
    str =  re.sub ('\\\\output', 'output = ',str)
    return str


@rule ((1, 0, 6), 'foo = \\translator {\\type .. } ->\\translator {\\type ..; foo; }')
def conv(str):
    if re.search ('[a-zA-Z]+ = *\\translator',str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % _ ("\\translator syntax"))
	stderr_write ('\n')
    #	raise FatalConversionError ()
    return str


@rule ((1, 0, 7), '\\lyric -> \\lyrics')
def conv(str):
    str =  re.sub ('\\\\lyrics*', '\\\\lyrics',str)
    return str


@rule ((1, 0, 10), '[2/3 ]1/1 -> \\times 2/3 ')
def conv(str):
    str =  re.sub ('\\\\\\[/3+', '\\\\times 2/3 { ',str)
    str =  re.sub ('\\[/3+', '\\\\times 2/3 { [',str)
    str =  re.sub ('\\\\\\[([0-9/]+)', '\\\\times \\1 {',str)
    str =  re.sub ('\\[([0-9/]+)', '\\\\times \\1 { [',str)
    str =  re.sub ('\\\\\\]([0-9/]+)', '}', str)
    str =  re.sub ('\\\\\\]', '}',str)
    str =  re.sub ('\\]([0-9/]+)', '] }', str)
    return str


@rule ((1, 0, 12), 'Chord syntax stuff')
def conv(str):
    return str


@rule ((1, 0, 13), '<a ~ b> c -> <a b> ~ c')
def conv(str):
    str =  re.sub ('<([^>~]+)~([^>]*)>','<\\1 \\2> ~', str)
    return str


@rule ((1, 0, 14), '<[a b> <a b]>c -> [<a b> <a b>]')
def conv(str):
    str =  re.sub ('<\\[','[<', str)
    str =  re.sub ('\\]>','>]', str)
    return str


@rule ((1, 0, 16), '\\type -> \\context, textstyle -> textStyle')
def conv(str):
    str =  re.sub ('\\\\type([^\n]*engraver)','\\\\TYPE\\1', str)
    str =  re.sub ('\\\\type([^\n]*performer)','\\\\TYPE\\1', str)
    str =  re.sub ('\\\\type','\\\\context', str)
    str =  re.sub ('\\\\TYPE','\\\\type', str)
    str =  re.sub ('textstyle','textStyle', str)
    return str


@rule ((1, 0, 18), _ ('\\repeat NUM Music Alternative -> \\repeat FOLDSTR Music Alternative'))
def conv(str):
    if re.search ('\\\\repeat',str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % "\\repeat")
	stderr_write ('\n')
    #	raise FatalConversionError ()
    return str


@rule ((1, 0, 19), 'fontsize -> fontSize, midi_instrument -> midiInstrument, SkipBars -> skipBars')
def conv(str):
    str =  re.sub ('SkipBars','skipBars', str)
    str =  re.sub ('fontsize','fontSize', str)
    str =  re.sub ('midi_instrument','midiInstrument', str)
    return str


@rule ((1, 0, 20), '{,tie,slur}ydirection -> {v,tieV,slurV}erticalDirection')
def conv(str):
    str =  re.sub ('tieydirection','tieVerticalDirection', str)
    str =  re.sub ('slurydirection','slurVerticalDirection', str)
    str =  re.sub ('ydirection','verticalDirection', str)
    return str


@rule ((1, 0, 21), 'hshift -> horizontalNoteShift')
def conv(str):
    str =  re.sub ('hshift','horizontalNoteShift', str)
    return str


@rule ((1, 1, 52), _ ('deprecate %s') % '\\grouping')
def conv(str):
    str =  re.sub ('\\\\grouping[^;]*;','', str)
    return str


@rule ((1, 1, 55), '\\wheel -> \\coda')
def conv(str):
    str =  re.sub ('\\\\wheel','\\\\coda', str)
    return str


@rule ((1, 1, 65), 'slurdash -> slurDash, keyoctaviation -> keyOctaviation')
def conv(str):
    str =  re.sub ('keyoctaviation','keyOctaviation', str)
    str =  re.sub ('slurdash','slurDash', str)
    return str


@rule ((1, 1, 66), 'semi -> volta')
def conv(str):
    str =  re.sub ('\\\\repeat *\"?semi\"?','\\\\repeat "volta"', str)
    return str


@rule ((1, 1, 67), 'beamAuto -> noAutoBeaming')
def conv(str):
    str =  re.sub ('\"?beamAuto\"? *= *\"?0?\"?','noAutoBeaming = "1"', str)
    return str


@rule ((1, 2, 0), 'automaticMelismas -> automaticMelismata')
def conv(str):
    str =  re.sub ('automaticMelismas', 'automaticMelismata', str)
    return str


@rule ((1, 2, 1), 'dynamicDir -> dynamicDirection')
def conv(str):
    str =  re.sub ('dynamicDir\\b', 'dynamicDirection', str)
    return str


@rule ((1, 3, 4), '\\cadenza -> \\cadenza{On|Off}')
def conv(str):
    str =  re.sub ('\\\\cadenza *0 *;', '\\\\cadenzaOff', str)
    str =  re.sub ('\\\\cadenza *1 *;', '\\\\cadenzaOn', str)
    return str


@rule ((1, 3, 5), 'beamAuto moment properties')
def conv (str):
    str = re.sub ('"?beamAuto([^"=]+)"? *= *"([0-9]+)/([0-9]+)" *;*',
		  'beamAuto\\1 = #(make-moment \\2 \\3)',
		  str)
    return str


@rule ((1, 3, 17), 'stemStyle -> flagStyle')
def conv (str):
    str = re.sub ('stemStyle',
		  'flagStyle',
		  str)
    return str


@rule ((1, 3, 18), 'staffLineLeading -> staffSpace')
def conv (str):
    str = re.sub ('staffLineLeading',
		  'staffSpace',
		  str)
    return str


@rule ((1, 3, 23), _ ('deprecate %s ') % '\\repetitions')
def conv(str):
    if re.search ('\\\\repetitions',str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % "\\repetitions")
	stderr_write ('\n')
    #	raise FatalConversionError ()
    return str


@rule ((1, 3, 35), 'textEmptyDimension -> textNonEmpty')
def conv (str):
    str = re.sub ('textEmptyDimension *= *##t',
		  'textNonEmpty = ##f',
		  str)
    str = re.sub ('textEmptyDimension *= *##f',
		  'textNonEmpty = ##t',
		  str)
    return str


@rule ((1, 3, 38), '\musicalpitch { a b c } -> #\'(a b c)')
def conv (str):
    str = re.sub ("([a-z]+)[ \t]*=[ \t]*\\\\musicalpitch *{([- 0-9]+)} *\n",
		  "(\\1 . (\\2))\n", str)
    str = re.sub ("\\\\musicalpitch *{([0-9 -]+)}",
		  "\\\\musicalpitch #'(\\1)", str)
    if re.search ('\\\\notenames',str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % _ ("new \\notenames format"))
	stderr_write ('\n')
    return str


@rule ((1, 3, 39), '\\key A ;  ->\\key a;')
def conv (str):
    def replace (match):
	return '\\key %s;' % match.group (1).lower ()

    str = re.sub ("\\\\key ([^;]+);",  replace, str)
    return str


@rule ((1, 3, 41), '[:16 c4 d4 ] -> \\repeat "tremolo" 2 { c16 d16 }')
def conv (str):
    if re.search ('\\[:',str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % _ ("new tremolo format"))
	stderr_write ('\n')
    return str


@rule ((1, 3, 42), _ ('Staff_margin_engraver deprecated, use Instrument_name_engraver'))
def conv (str):
    str = re.sub ('Staff_margin_engraver' , 'Instrument_name_engraver', str)
    return str


@rule ((1, 3, 49), 'noteHeadStyle value: string -> symbol')
def conv (str):
    str = re.sub ('note[hH]eadStyle\\s*=\\s*"?(\\w+)"?' , "noteHeadStyle = #'\\1", str)
    return str


@rule ((1, 3, 58), 'noteHeadStyle value: string -> symbol')
def conv (str):
    if re.search ('\\\\keysignature', str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % '\\keysignature')
	stderr_write ('\n')
    return str


@rule ((1, 3, 59), '\key X ; -> \key X major; ')
def conv (str):
    str = re.sub (r"""\\key *([a-z]+) *;""", r"""\\key \1 \major;""",str);
    return str


@rule ((1, 3, 68), 'latexheaders = "\\input global" -> latexheaders = "global"')
def conv (str):
    str = re.sub (r'latexheaders *= *"\\\\input ',
		  'latexheaders = "',
		  str)
    return str


# TODO: lots of other syntax changes should be done here as well
@rule ((1, 3, 92), 'basicXXXProperties -> XXX, Repeat_engraver -> Volta_engraver')
def conv (str):
    str = re.sub ('basicCollisionProperties', 'NoteCollision', str)
    str = re.sub ('basicVoltaSpannerProperties' , "VoltaBracket", str)
    str = re.sub ('basicKeyProperties' , "KeySignature", str)

    str = re.sub ('basicClefItemProperties' ,"Clef", str)


    str = re.sub ('basicLocalKeyProperties' ,"Accidentals", str)
    str = re.sub ('basicMarkProperties' ,"Accidentals", str)
    str = re.sub ('basic([A-Za-z_]+)Properties', '\\1', str)

    str = re.sub ('Repeat_engraver' ,'Volta_engraver', str)
    return str


@rule ((1, 3, 93), _ ('change property definiton case (eg. onevoice -> oneVoice)'))
def conv (str):
    # Ugh, but meaning of \stemup changed too
    # maybe we should do \stemup -> \stemUp\slurUp\tieUp ?
    str = re.sub ('\\\\stemup', '\\\\stemUp', str)
    str = re.sub ('\\\\stemdown', '\\\\stemDown', str)
    str = re.sub ('\\\\stemboth', '\\\\stemBoth', str)

    str = re.sub ('\\\\slurup', '\\\\slurUp', str)
    str = re.sub ('\\\\slurboth', '\\\\slurBoth', str)
    str = re.sub ('\\\\slurdown', '\\\\slurDown', str)
    str = re.sub ('\\\\slurdotted', '\\\\slurDotted', str)
    str = re.sub ('\\\\slurnormal', '\\\\slurNoDots', str)

    str = re.sub ('\\\\shiftoff', '\\\\shiftOff', str)
    str = re.sub ('\\\\shifton', '\\\\shiftOn', str)
    str = re.sub ('\\\\shiftonn', '\\\\shiftOnn', str)
    str = re.sub ('\\\\shiftonnn', '\\\\shiftOnnn', str)

    str = re.sub ('\\\\onevoice', '\\\\oneVoice', str)
    str = re.sub ('\\\\voiceone', '\\\\voiceOne', str)
    str = re.sub ('\\\\voicetwo', '\\\\voiceTwo', str)
    str = re.sub ('\\\\voicethree', '\\\\voiceThree', str)
    str = re.sub ('\\\\voicefour', '\\\\voiceFour', str)

    # I don't know exactly when these happened...
    # ugh, we lose context setting here...
    str = re.sub ('\\\\property *[^ ]*verticalDirection[^=]*= *#?"?(1|(\\\\up))"?', '\\\\stemUp\\\\slurUp\\\\tieUp', str)
    str = re.sub ('\\\\property *[^ ]*verticalDirection[^=]*= *#?"?((-1)|(\\\\down))"?', '\\\\stemDown\\\\slurDown\\\\tieDown', str)
    str = re.sub ('\\\\property *[^ ]*verticalDirection[^=]*= *#?"?(0|(\\\\center))"?', '\\\\stemBoth\\\\slurBoth\\\\tieBoth', str)

    str = re.sub ('verticalDirection[^=]*= *#?"?(1|(\\\\up))"?', 'Stem \\\\override #\'direction = #0\nSlur \\\\override #\'direction = #0\n Tie \\\\override #\'direction = #1', str)
    str = re.sub ('verticalDirection[^=]*= *#?"?((-1)|(\\\\down))"?', 'Stem \\\\override #\'direction = #0\nSlur \\\\override #\'direction = #0\n Tie \\\\override #\'direction = #-1', str)
    str = re.sub ('verticalDirection[^=]*= *#?"?(0|(\\\\center))"?', 'Stem \\\\override #\'direction = #0\nSlur \\\\override #\'direction = #0\n Tie \\\\override #\'direction = #0', str)

    str = re.sub ('\\\\property *[^ .]*[.]?([a-z]+)VerticalDirection[^=]*= *#?"?(1|(\\\\up))"?', '\\\\\\1Up', str)
    str = re.sub ('\\\\property *[^ .]*[.]?([a-z]+)VerticalDirection[^=]*= *#?"?((-1)|(\\\\down))"?', '\\\\\\1Down', str)
    str = re.sub ('\\\\property *[^ .]*[.]?([a-z]+)VerticalDirection[^=]*= *#?"?(0|(\\\\center))"?', '\\\\\\1Both', str)

    # (lacks capitalization slur -> Slur)
    str = re.sub ('([a-z]+)VerticalDirection[^=]*= *#?"?(1|(\\\\up))"?', '\\1 \\\\override #\'direction = #1', str)
    str = re.sub ('([a-z]+)VerticalDirection[^=]*= *#?"?((-1)|(\\\\down))"?', '\\1 \\override #\'direction = #-1', str)
    str = re.sub ('([a-z]+)VerticalDirection[^=]*= *#?"?(0|(\\\\center))"?', '\\1 \\\\override #\'direction = #0', str)

    ## dynamic..
    str = re.sub ('\\\\property *[^ .]*[.]?dynamicDirection[^=]*= *#?"?(1|(\\\\up))"?', '\\\\dynamicUp', str)
    str = re.sub ('\\\\property *[^ .]*[.]?dyn[^=]*= *#?"?((-1)|(\\\\down))"?', '\\\\dynamicDown', str)
    str = re.sub ('\\\\property *[^ .]*[.]?dyn[^=]*= *#?"?(0|(\\\\center))"?', '\\\\dynamicBoth', str)

    str = re.sub ('\\\\property *[^ .]*[.]?([a-z]+)Dash[^=]*= *#?"?(0|(""))"?', '\\\\\\1NoDots', str)
    str = re.sub ('\\\\property *[^ .]*[.]?([a-z]+)Dash[^=]*= *#?"?([1-9]+)"?', '\\\\\\1Dotted', str)

    str = re.sub ('\\\\property *[^ .]*[.]?noAutoBeaming[^=]*= *#?"?(0|(""))"?', '\\\\autoBeamOn', str)
    str = re.sub ('\\\\property *[^ .]*[.]?noAutoBeaming[^=]*= *#?"?([1-9]+)"?', '\\\\autoBeamOff', str)
    return str


@rule ((1, 3, 97), 'ChordName -> ChordNames')
def conv (str):
    str = re.sub ('ChordNames*', 'ChordNames', str)
    if re.search ('\\\\textscript "[^"]* *"[^"]*"', str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % _ ("new \\textscript markup text"))
	stderr_write ('\n')

    str = re.sub ('\\textscript +("[^"]*")', '\\textscript #\\1', str)
    return str

# TODO: add lots of these

@rule ((1, 3, 98), 'CONTEXT.textStyle -> GROB.#font-style ')
def conv (str):
    str = re.sub ('\\\\property *"?Voice"? *[.] *"?textStyle"? *= *"([^"]*)"', '\\\\property Voice.TextScript \\\\set #\'font-style = #\'\\1', str)
    str = re.sub ('\\\\property *"?Lyrics"? *[.] *"?textStyle"? *= *"([^"]*)"', '\\\\property Lyrics.LyricText \\\\set #\'font-style = #\'\\1', str)

    str = re.sub ('\\\\property *"?([^.]+)"? *[.] *"?timeSignatureStyle"? *= *"([^"]*)"', '\\\\property \\1.TimeSignature \\\\override #\'style = #\'\\2', str)

    str = re.sub ('"?timeSignatureStyle"? *= *#?""', 'TimeSignature \\\\override #\'style = ##f', str)

    str = re.sub ('"?timeSignatureStyle"? *= *#?"([^"]*)"', 'TimeSignature \\\\override #\'style = #\'\\1', str)

    str = re.sub ('#\'style *= #*"([^"])"', '#\'style = #\'\\1', str)

    str = re.sub ('\\\\property *"?([^.]+)"? *[.] *"?horizontalNoteShift"? *= *"?#?([-0-9]+)"?', '\\\\property \\1.NoteColumn \\\\override #\'horizontal-shift = #\\2', str)

    # ugh
    str = re.sub ('\\\\property *"?([^.]+)"? *[.] *"?flagStyle"? *= *""', '\\\\property \\1.Stem \\\\override #\'flag-style = ##f', str)

    str = re.sub ('\\\\property *"?([^.]+)"? *[.] *"?flagStyle"? *= *"([^"]*)"', '\\\\property \\1.Stem \\\\override #\'flag-style = #\'\\2', str)
    return str


@rule ((1, 3, 102), 'beamAutoEnd -> autoBeamSettings \\push (end * * * *)')
def conv (str):
    str = re.sub ('"?beamAutoEnd_([0-9]*)"? *= *(#\\([^)]*\\))', 'autoBeamSettings \\push #\'(end 1 \\1 * *) = \\2', str)
    str = re.sub ('"?beamAutoBegin_([0-9]*)"? *= *(#\\([^)]*\))', 'autoBeamSettings \\push #\'(begin 1 \\1 * *) = \\2', str)
    str = re.sub ('"?beamAutoEnd"? *= *(#\\([^)]*\\))', 'autoBeamSettings \\push #\'(end * * * *) = \\1', str)
    str = re.sub ('"?beamAutoBegin"? *= *(#\\([^)]*\\))', 'autoBeamSettings \\push #\'(begin * * * *) = \\1', str)
    return str


@rule ((1, 3, 111), '\\push -> \\override, \\pop -> \\revert')
def conv (str):
    str = re.sub ('\\\\push', '\\\\override', str)
    str = re.sub ('\\\\pop', '\\\\revert', str)
    return str


@rule ((1, 3, 113), 'LyricVoice -> LyricsVoice')
def conv (str):
    str = re.sub ('LyricVoice', 'LyricsVoice', str)
    # old fix
    str = re.sub ('Chord[Nn]ames*.Chord[Nn]ames*', 'ChordNames.ChordName', str)
    str = re.sub ('Chord[Nn]ames([ \t\n]+\\\\override)', 'ChordName\\1', str)
    return str


def regularize_id (str):
    s = ''
    lastx = ''
    for x in str:
        if x == '_':
            lastx = x
            continue
        elif x in string.digits:
            x = chr(ord (x) - ord ('0')  +ord ('A'))
        elif x not in string.letters:
            x = 'x'
        elif x in string.lowercase and lastx == '_':
            x = x.upper ()
        s = s + x
        lastx = x
    return s


@rule ((1, 3, 117), _ ('identifier names: %s') % '$!foo_bar_123 -> xfooBarABC')
def conv (str):
    def regularize_dollar_reference (match):
	return regularize_id (match.group (1))
    def regularize_assignment (match):
	return '\n' + regularize_id (match.group (1)) + ' = '
    str = re.sub ('\$([^\t\n ]+)', regularize_dollar_reference, str)
    str = re.sub ('\n([^ \t\n]+)[ \t]*= *', regularize_assignment, str)
    return str


@rule ((1, 3, 120), 'paper_xxx -> paperXxxx, pedalup -> pedalUp.')
def conv (str):
    def regularize_paper (match):
	return regularize_id (match.group (1))
    str = re.sub ('(paper_[a-z]+)', regularize_paper, str)
    str = re.sub ('sustainup', 'sustainUp', str)
    str = re.sub ('nobreak', 'noBreak', str)
    str = re.sub ('sustaindown', 'sustainDown', str)
    str = re.sub ('sostenutoup', 'sostenutoUp', str)
    str = re.sub ('sostenutodown', 'sostenutoDown', str)
    str = re.sub ('unachorda', 'unaChorda', str)
    str = re.sub ('trechorde', 'treChorde', str)
    return str


@rule ((1, 3, 122), 'drarnChords -> chordChanges, \\musicalpitch -> \\pitch')
def conv (str):
    str = re.sub ('drarnChords', 'chordChanges', str)
    str = re.sub ('\\musicalpitch', '\\pitch', str)
    return str


@rule ((1, 3, 136), 'ly-X-elt-property -> ly-X-grob-property')
def conv (str):
    str = re.sub ('ly-([sg])et-elt-property', 'ly-\\1et-grob-property', str)
    return str


@rule ((1, 3, 138), _ ('point-and-click argument changed to procedure.'))
def conv (str):
    str = re.sub ('point-and-click +#t', 'point-and-click line-column-location', str)
    return str


@rule ((1, 3, 138), 'followThread -> followVoice.')
def conv (str):
    str = re.sub ('followThread', 'followVoice', str)
    str = re.sub ('Thread.FollowThread', 'Voice.VoiceFollower', str)
    str = re.sub ('FollowThread', 'VoiceFollower', str)
    return str


@rule ((1, 3, 139), 'font-point-size -> font-design-size.')
def conv (str):
    str = re.sub ('font-point-size', 'font-design-size', str)
    return str


@rule ((1, 3, 141), 'xNoDots -> xSolid')
def conv (str):
    str = re.sub ('([a-zA-Z]*)NoDots', '\\1Solid', str)
    return str


@rule ((1, 3, 144), 'Chorda -> Corda')
def conv (str):
    str = re.sub ('([Cc])hord([ea])', '\\1ord\\2', str)
    return str


@rule ((1, 3, 145), 'ContextNameXxxxVerticalExtent -> XxxxVerticalExtent')
def conv (str):
    str = re.sub ('([A-Za-z]+)MinimumVerticalExtent', 'MinimumV@rticalExtent', str)
    str = re.sub ('([A-Za-z]+)ExtraVerticalExtent', 'ExtraV@rticalExtent', str)
    str = re.sub ('([A-Za-z]+)VerticalExtent', 'VerticalExtent', str)
    str = re.sub ('ExtraV@rticalExtent', 'ExtraVerticalExtent', str)
    str = re.sub ('MinimumV@rticalExtent', 'MinimumVerticalExtent', str)
    return str


@rule ((1, 3, 146), _('semicolons removed'))
def conv (str):
    str = re.sub ('\\\\key[ \t]*;', '\\key \\default;', str)
    str = re.sub ('\\\\mark[ \t]*;', '\\mark \\default;', str)

    # Make sure groups of more than one ; have space before
    # them, so that non of them gets removed by next rule
    str = re.sub ("([^ \n\t;]);(;+)", "\\1 ;\\2", str)

    # Only remove ; that are not after spaces, # or ;
    # Otherwise  we interfere with Scheme comments,
    # which is badbadbad.
    str = re.sub ("([^ \t;#]);", "\\1", str)
    return str


@rule ((1, 3, 147), 'default-neutral-direction -> neutral-direction')
def conv (str):
    str = re.sub ('default-neutral-direction', 'neutral-direction',str)
    return str


@rule ((1, 3, 148), '"(align" -> "(axis", "(rows" -> "(columns"')
def conv (str):
    str = re.sub ('\(align', '(axis', str)
    str = re.sub ('\(rows', '(columns', str)
    return str


@rule ((1, 5, 33), 'SystemStartDelimiter -> systemStartDelimiter')
def conv (str):
    str = re.sub ('SystemStartDelimiter', 'systemStartDelimiter', str)
    return str


@rule ((1, 5, 38), 'arithmetic... -> spacing...')
def conv (str):
    str = re.sub ('arithmetic-multiplier', 'spacing-increment', str)
    str = re.sub ('arithmetic-basicspace', 'shortest-duration-space', str)
    return str


# 40 ?
@rule ((1, 5, 40), _ ('%s property names') % 'breakAlignOrder')
def conv (str):

    def func(match):
	break_dict = {
	"Instrument_name": "instrument-name",
	"Left_edge_item": "left-edge",
	"Span_bar": "span-bar",
	"Breathing_sign": "breathing-sign",
	"Staff_bar": "staff-bar",
	"Clef_item": "clef",
	"Key_item": "key-signature",
	"Time_signature": "time-signature",
	"Custos": "custos"
	}
	props =  match.group (1)
	for (k,v) in break_dict.items():
	    props = re.sub (k, v, props)
	return  "breakAlignOrder = #'(%s)" % props

    str = re.sub ("breakAlignOrder *= *#'\\(([a-z_\n\tA-Z ]+)\\)",
		  func, str)
    return str


@rule ((1, 5, 49), 'noAutoBeaming -> autoBeaming')
def conv (str):
    str = re.sub ('noAutoBeaming *= *##f', 'autoBeaming = ##t', str)
    str = re.sub ('noAutoBeaming *= *##t', 'autoBeaming = ##f', str)
    return str


@rule ((1, 5, 52), 'tuplet-X-visibility -> X-visibility')
def conv (str):
    str = re.sub ('tuplet-bracket-visibility', 'bracket-visibility', str)
    str = re.sub ('tuplet-number-visibility', 'number-visibility', str)
    return str


@rule ((1, 5, 56), 'Pitch::transpose -> ly-transpose-pitch')
def conv (str):
    str = re.sub ('Pitch::transpose', 'ly-transpose-pitch', str)
    return str


@rule ((1, 5, 58), _ ('deprecate %s') % 'textNonEmpty')
def conv (str):
    str = re.sub ('textNonEmpty *= *##t', "TextScript \\set #'no-spacing-rods = ##f", str)
    str = re.sub ('textNonEmpty *= *##f', "TextScript \\set #'no-spacing-rods = ##t", str)
    return str


@rule ((1, 5, 59), 'XxxxVerticalExtent -> xxxVerticalExtent')
def conv (str):
    str = re.sub ('MinimumVerticalExtent', 'minimumV@rticalExtent', str)
    str = re.sub ('minimumVerticalExtent', 'minimumV@rticalExtent', str)
    str = re.sub ('ExtraVerticalExtent', 'extraV@rticalExtent', str)
    str = re.sub ('extraVerticalExtent', 'extraV@rticalExtent', str)
    str = re.sub ('VerticalExtent', 'verticalExtent', str)
    str = re.sub ('extraV@rticalExtent', 'extraVerticalExtent', str)
    str = re.sub ('minimumV@rticalExtent', 'minimumVerticalExtent', str)
    return str


@rule ((1, 5, 62), 'visibility-lambda -> break-visibility')
def conv (str):
    str = re.sub ('visibility-lambda', 'break-visibility', str)
    return str


@rule ((1, 5, 67), _ ('automaticMelismata turned on by default'))
def conv (str):
    if re.search (r'\addlyrics',str) \
	   and re.search ('automaticMelismata', str)  == None:
	stderr_write ('\n')
	stderr_write (NOT_SMART % "automaticMelismata; turned on by default since 1.5.67.")
	stderr_write ('\n')
	raise FatalConversionError ()
    return str


@rule ((1, 5, 68), 'ly-set-X-property -> ly-set-X-property!')
def conv (str):
    str = re.sub ('ly-set-grob-property([^!])', 'ly-set-grob-property!\1', str)
    str = re.sub ('ly-set-mus-property([^!])', 'ly-set-mus-property!\1', str)
    return str


@rule ((1, 5, 71), 'extent-[XY] -> [XY]-extent')
def conv (str):
    str = re.sub ('extent-X', 'X-extent', str)
    str = re.sub ('extent-Y', 'Y-extent', str)
    return str


@rule ((1, 5, 72), 'set! point-and-click -> set-point-and-click!')
def conv (str):
    str = re.sub ("""#\(set! +point-and-click +line-column-location\)""",
		  """#(set-point-and-click! \'line-column)""", str)
    str = re.sub ("""#\(set![ \t]+point-and-click +line-location\)""",
		  '#(set-point-and-click! \'line)', str)
    str = re.sub ('#\(set! +point-and-click +#f\)',
		  '#(set-point-and-click! \'none)', str)
    return str


@rule ((1, 6, 5), 'Stems: flag-style -> stroke-style; style -> flag-style')
def conv (str):
    str = re.sub ('flag-style', 'stroke-style', str)
    str = re.sub (r"""Stem([ ]+)\\override #'style""", r"""Stem \\override #'flag-style""", str);
    str = re.sub (r"""Stem([ ]+)\\set([ ]+)#'style""", r"""Stem \\set #'flag-style""", str);
    return str


def subst_req_name (match):
    return "(make-music-by-name \'%sEvent)" % regularize_id (match.group(1))


@rule ((1, 7, 1), 'ly-make-music foo_bar_req -> make-music-by-name FooBarEvent')
def conv (str):
    str = re.sub ('\\(ly-make-music *\"([A-Z][a-z_]+)_req\"\\)', subst_req_name, str)
    str = re.sub ('Request_chord', 'EventChord', str)
    return str


spanner_subst ={
	"text" : 'TextSpanEvent',
	"decrescendo" : 'DecrescendoEvent',
	"crescendo" : 'CrescendoEvent',
	"Sustain" : 'SustainPedalEvent',
	"slur" : 'SlurEvent',
	"UnaCorda" : 'UnaCordaEvent',
	"Sostenuto" : 'SostenutoEvent',
	}

def subst_ev_name (match):
    stype = 'STOP'
    if re.search ('start', match.group(1)):
	stype= 'START'
    mtype = spanner_subst[match.group(2)]
    return "(make-span-event '%s %s)" % (mtype , stype)

def subst_definition_ev_name(match):
    return ' = #%s' % subst_ev_name (match)

def subst_inline_ev_name (match):
    s = subst_ev_name (match)
    return '#(ly-export %s)' % s

def subst_csp_definition (match):
    return ' = #(make-event-chord (list %s))' % subst_ev_name (match)

def subst_csp_inline (match):
    return '#(ly-export (make-event-chord (list %s)))' % subst_ev_name (match)


@rule ((1, 7, 2), '\\spanrequest -> #(make-span-event .. ), \script -> #(make-articulation .. )')
def conv (str):
    str = re.sub (r' *= *\\spanrequest *([^ ]+) *"([^"]+)"', subst_definition_ev_name, str)
    str = re.sub (r'\\spanrequest *([^ ]+) *"([^"]+)"', subst_inline_ev_name, str)
    str = re.sub (r' *= *\\commandspanrequest *([^ ]+) *"([^"]+)"', subst_csp_definition, str)
    str = re.sub (r'\\commandspanrequest *([^ ]+) *"([^"]+)"', subst_csp_inline, str)
    str = re.sub (r'ly-id ', 'ly-import ', str)

    str = re.sub (r' *= *\\script "([^"]+)"', ' = #(make-articulation "\\1")', str)
    str = re.sub (r'\\script "([^"]+)"', '#(ly-export (make-articulation "\\1"))', str)
    return str


@rule ((1, 7, 3), 'ly- -> ly:')
def conv(str):
    str = re.sub (r'\(ly-', '(ly:', str)

    changed = [
	    r'duration\?',
	    r'font-metric\?',
	    r'molecule\?',
	    r'moment\?',
	    r'music\?',
	    r'pitch\?',
	    'make-duration',
	    'music-duration-length',
	    'duration-log',
	    'duration-dotcount',
	    'intlog2',
	    'duration-factor',
	    'transpose-key-alist',
	    'get-system',
	    'get-broken-into',
	    'get-original',
	    'set-point-and-click!',
	    'make-moment',
	    'make-pitch',
	    'pitch-octave',
	    'pitch-alteration',
	    'pitch-notename',
	    'pitch-semitones',
	    r'pitch<\?',
	    r'dir\?',
	    'music-duration-compress',
	    'set-point-and-click!'
	    ]

    origre = r'\b(%s)' % '|'.join (changed)

    str = re.sub (origre, r'ly:\1',str)
    str = re.sub ('set-point-and-click!', 'set-point-and-click', str)
    return str


@rule ((1, 7, 4), '<< >> -> < <  > >')
def conv(str):
    if re.search ('new-chords-done',str):
	return str

    str = re.sub (r'<<', '< <', str)
    str = re.sub (r'>>', '> >', str)
    return str


@rule ((1, 7, 5), '\\transpose TO -> \\transpose FROM  TO')
def conv(str):
    str = re.sub (r"\\transpose", r"\\transpose c'", str)
    str = re.sub (r"\\transpose c' *([a-z]+)'", r"\\transpose c \1", str)
    return str


@rule ((1, 7, 6), 'note\\script -> note-\script')
def conv(str):
    kws =   ['arpeggio',
	     'sustainDown',
	     'sustainUp',
	     'f',
	     'p',
	     'pp',
	     'ppp',
	     'fp',
	     'ff',
	     'mf',
	     'mp',
	     'sfz',
	     ]

    origstr = '|'.join (kws)
    str = re.sub (r'([^_^-])\\(%s)\b' % origstr, r'\1-\\\2', str)
    return str


@rule ((1, 7, 10), "\property ChordName #'style -> #(set-chord-name-style 'style)")
def conv(str):
    str = re.sub (r"\\property *ChordNames *\. *ChordName *\\(set|override) *#'style *= *#('[a-z]+)",
		  r"#(set-chord-name-style \2)", str)
    str = re.sub (r"\\property *ChordNames *\. *ChordName *\\revert *#'style",
		  r"", str)
    return str


@rule ((1, 7, 11), "transpose-pitch -> pitch-transpose")
def conv(str):
    str = re.sub (r"ly:transpose-pitch", "ly:pitch-transpose", str)
    return str


@rule ((1, 7, 13), "ly:XX-molecule-YY -> ly:molecule-XX-YY")
def conv(str):
    str = re.sub (r"ly:get-molecule-extent", "ly:molecule-get-extent", str)
    str = re.sub (r"ly:set-molecule-extent!", "ly:molecule-set-extent!", str)
    str = re.sub (r"ly:add-molecule", "ly:molecule-add", str)
    str = re.sub (r"ly:combine-molecule-at-edge", "ly:molecule-combine-at-edge", str)
    str = re.sub (r"ly:align-to!", "ly:molecule-align-to!", str)
    return str


@rule ((1, 7, 15), "linewidth = -1 -> raggedright = ##t")
def conv(str):
    str = re.sub (r"linewidth *= *-[0-9.]+ *(\\mm|\\cm|\\in|\\pt)?", 'raggedright = ##t', str )
    return str


@rule ((1, 7, 16), "divisiomaior -> divisioMaior")
def conv(str):
    str = re.sub ("divisiomaior",
		  "divisioMaior", str)
    str = re.sub ("divisiominima",
		  "divisioMinima", str)
    str = re.sub ("divisiomaxima",
		  "divisioMaxima", str)
    return str


@rule ((1, 7, 17), "Skip_req  -> Skip_event")
def conv(str):
    str = re.sub ("Skip_req_swallow_translator",
		  "Skip_event_swallow_translator", str)
    return str


@rule ((1, 7, 18), "groupOpen/Close  -> start/stopGroup, #'outer  -> #'enclose-bounds")
def conv(str):
    str = re.sub ("groupOpen",
		  "startGroup", str)
    str = re.sub ("groupClose",
		  "stopGroup", str)
    str = re.sub ("#'outer",
		  "#'enclose-bounds", str)

    return str


@rule ((1, 7, 19), _ ("remove %s") % "GraceContext")
def conv(str):
    if re.search( r'\\GraceContext', str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % "GraceContext")
	stderr_write (FROM_TO \
			  % ("GraceContext", "#(add-to-grace-init .. )"))
	stderr_write ('\n')
	stderr_write (UPDATE_MANUALLY)
	stderr_write ('\n')
	raise FatalConversionError ()

    str = re.sub ('HaraKiriStaffContext', 'RemoveEmptyStaffContext', str)
    return str


@rule ((1, 7, 22), "#'type -> #'style")
def conv(str):
    str = re.sub (
	    r"(set|override|revert) *#'type",
	    r"\1 #'style",
	    str)
    return str


@rule ((1, 7, 23), "barNonAuto -> automaticBars")
def conv(str):
    str = re.sub (
	    "barNonAuto *= *##t",
	    "automaticBars = ##f",
	    str)
    str = re.sub (
	    "barNonAuto *= *##f",
	    "automaticBars = ##t",
	    str)
    return str


@rule ((1, 7, 24), _ ("cluster syntax"))
def conv(str):
    if re.search( r'-(start|stop)Cluster', str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % _ ("cluster syntax"))
	stderr_write ('\n')
	stderr_write (UPDATE_MANUALLY)
	stderr_write ('\n')

	raise FatalConversionError ()
    return str


@rule ((1, 7, 28), _ ("new Pedal style syntax"))
def conv(str):
    str = re.sub (r"\\property *Staff\.(Sustain|Sostenuto|UnaCorda)Pedal *\\(override|set) *#'pedal-type *",
		    r"\property Staff.pedal\1Style ", str)
    str = re.sub (r"\\property *Staff\.(Sustain|Sostenuto|UnaCorda)Pedal *\\revert *#'pedal-type", '', str)
    return str


def sub_chord (m):
    str = m.group(1)

    origstr =  '<%s>' % str
    if re.search (r'\\\\', str):
	return origstr

    if re.search (r'\\property', str):
	return origstr

    if re.match (r'^\s*\)?\s*\\[a-zA-Z]+', str):
	return origstr

    durs = []
    def sub_durs (m, durs = durs):
	durs.append(m.group(2))
	return m.group (1)

    str = re.sub (r"([a-z]+[,'!? ]*)([0-9]+\.*)", sub_durs, str)
    dur_str = ''

    for d in durs:
	if dur_str == '':
	    dur_str = d
	if dur_str <> d:
	    return '<%s>' % m.group (1)

    pslur_strs = ['']
    dyns = ['']
    slur_strs = ['']

    last_str = ''
    while last_str <> str:
	last_str = str

	def sub_tremolos (m, slur_strs = slur_strs):
	    tr = m.group (2)
	    if tr not in slur_strs:
		slur_strs.append (tr)
	    return  m.group (1)

	str = re.sub (r"([a-z]+[',!? ]*)(:[0-9]+)",
		      sub_tremolos, str)

	def sub_dyn_end (m, dyns = dyns):
	    dyns.append (' \!')
	    return ' ' + m.group(2)

	str = re.sub (r'(\\!)\s*([a-z]+)', sub_dyn_end, str)
	def sub_slurs(m, slur_strs = slur_strs):
	    if '-)' not in slur_strs:
		slur_strs.append (')')
	    return m.group(1)

	def sub_p_slurs(m, slur_strs = slur_strs):
	    if '-\)' not in slur_strs:
		slur_strs.append ('\)')
	    return m.group(1)

	str = re.sub (r"\)[ ]*([a-z]+)", sub_slurs, str)
	str = re.sub (r"\\\)[ ]*([a-z]+)", sub_p_slurs, str)
	def sub_begin_slurs(m, slur_strs = slur_strs):
	    if '-(' not in slur_strs:
		slur_strs.append ('(')
	    return m.group(1)

	str = re.sub (r"([a-z]+[,'!?0-9 ]*)\(",
		      sub_begin_slurs, str)
	def sub_begin_p_slurs(m, slur_strs = slur_strs):
	    if '-\(' not in slur_strs:
		slur_strs.append ('\(')
	    return m.group(1)

	str = re.sub (r"([a-z]+[,'!?0-9 ]*)\\\(",
		sub_begin_p_slurs, str)

	def sub_dyns (m, slur_strs = slur_strs):
	    s = m.group(0)
	    if s == '@STARTCRESC@':
		slur_strs.append ("\\<")
	    elif s == '@STARTDECRESC@':
		slur_strs.append ("\\>")
	    elif s == r'-?\\!':
		slur_strs.append ('\\!')
	    return ''

	str = re.sub (r'@STARTCRESC@', sub_dyns, str)
	str = re.sub (r'-?\\!', sub_dyns, str)

	def sub_articulations (m, slur_strs = slur_strs):
	    a = m.group(1)
	    if a not in slur_strs:
		slur_strs.append (a)
	    return ''

	str = re.sub (r"([_^-]\@ACCENT\@)", sub_articulations,
		      str)
	str = re.sub (r"([_^-]\\[a-z]+)", sub_articulations,
		      str)
	str = re.sub (r"([_^-][>_.+|^-])", sub_articulations,
		      str)
	str = re.sub (r'([_^-]"[^"]+")', sub_articulations,
		      str)

	def sub_pslurs(m, slur_strs = slur_strs):
	    slur_strs.append (' \\)')
	    return m.group(1)
	str = re.sub (r"\\\)[ ]*([a-z]+)", sub_pslurs, str)

    ## end of while <>

    suffix = ''.join (slur_strs) + ''.join (pslur_strs) \
	     + ''.join (dyns)

    return '@STARTCHORD@%s@ENDCHORD@%s%s' % (str , dur_str, suffix)



def sub_chords (str):
    simend = '>'
    simstart = '<'
    chordstart = '<<'
    chordend = '>>'
    marker_str = '%% new-chords-done %%'

    if re.search (marker_str,str):
	return str
    str = re.sub ('<<', '@STARTCHORD@', str)
    str = re.sub ('>>', '@ENDCHORD@', str)

    str = re.sub (r'\\<', '@STARTCRESC@', str)
    str = re.sub (r'\\>', '@STARTDECRESC@', str)
    str = re.sub (r'([_^-])>', r'\1@ACCENT@', str)
    str = re.sub (r'<([^<>{}]+)>', sub_chord, str)

    # add dash: -[, so that [<<a b>> c d] becomes
    #                      <<a b>>-[ c d]
    # and gets skipped by articulation_substitute
    str = re.sub (r'\[ *(@STARTCHORD@[^@]+@ENDCHORD@[0-9.]*)',
		  r'\1-[', str)
    str = re.sub (r'\\! *(@STARTCHORD@[^@]+@ENDCHORD@[0-9.]*)',
		  r'\1-\\!', str)

    str = re.sub (r'<([^?])', r'%s\1' % simstart, str)
    str = re.sub (r'>([^?])', r'%s\1' % simend,  str)
    str = re.sub ('@STARTCRESC@', r'\\<', str)
    str = re.sub ('@STARTDECRESC@', r'\\>' ,str)
    str = re.sub (r'\\context *Voice *@STARTCHORD@',
		  '@STARTCHORD@', str)
    str = re.sub ('@STARTCHORD@', chordstart, str)
    str = re.sub ('@ENDCHORD@', chordend, str)
    str = re.sub (r'@ACCENT@', '>', str)
    return str

markup_start = re.compile(r"([-^_]|\\mark)\s*(#\s*'\s*)\(")
musicglyph = re.compile(r"\(\s*music\b")
columns = re.compile(r"\(\s*columns\b")
submarkup_start = re.compile(r"\(\s*([a-zA-Z]+)")
leftpar = re.compile(r"\(")
rightpar = re.compile(r"\)")

def text_markup (str):
    result = ''
    # Find the beginning of each markup:
    match = markup_start.search (str)
    while match:
	result = result + str[:match.end (1)] + " \markup"
	str = str[match.end( 2):]
	# Count matching parentheses to find the end of the 
	# current markup:
	nesting_level = 0
	pars = re.finditer(r"[()]",str)
	for par in pars:
	    if par.group () == '(':
		nesting_level = nesting_level + 1
	    else:
		nesting_level = nesting_level - 1
	    if nesting_level == 0:
		markup_end = par.end ()
		break
	# The full markup in old syntax:
	markup = str[:markup_end]
	# Modify to new syntax:
	markup = musicglyph.sub (r"{\\musicglyph", markup)
	markup = columns.sub (r"{", markup)
	markup = submarkup_start.sub (r"{\\\1", markup)
	markup = leftpar.sub ("{", markup)
	markup = rightpar.sub ("}", markup)

	result = result + markup
	# Find next markup
	str = str[markup_end:]
	match = markup_start.search(str)
    result = result + str
    return result

def articulation_substitute (str):
    str = re.sub (r"""([^-])\[ *(\\?\)?[a-z]+[,']*[!?]?[0-9:]*\.*)""",
		  r"\1 \2[", str)
    str = re.sub (r"""([^-])\\\) *([a-z]+[,']*[!?]?[0-9:]*\.*)""",
		  r"\1 \2\\)", str)
    str = re.sub (r"""([^-\\])\) *([a-z]+[,']*[!?]?[0-9:]*\.*)""",
		  r"\1 \2)", str)
    str = re.sub (r"""([^-])\\! *([a-z]+[,']*[!?]?[0-9:]*\.*)""",
		  r"\1 \2\\!", str)
    return str

string_or_scheme = re.compile ('("(?:[^"\\\\]|\\\\.)*")|(#\\s*\'?\\s*\\()')

# Only apply articulation_substitute () outside strings and 
# Scheme expressions:
def smarter_articulation_subst (str):
    result = ''
    # Find the beginning of next string or Scheme expr.:
    match = string_or_scheme.search (str)
    while match:
	# Convert the preceding LilyPond code:
	previous_chunk = str[:match.start()]
	result = result + articulation_substitute (previous_chunk)
	if match.group (1): # Found a string
	    # Copy the string to output:
	    result = result + match.group (1)
	    str = str[match.end(1):]
	else: # Found a Scheme expression. Count 
	    # matching parentheses to find its end
	    str = str[match.start ():]
	    nesting_level = 0
	    pars = re.finditer(r"[()]",str)
	    for par in pars:
		if par.group () == '(':
		    nesting_level = nesting_level + 1
		else:
		    nesting_level = nesting_level - 1
		if nesting_level == 0:
		    scheme_end = par.end ()
		    break
	    # Copy the Scheme expression to output:
	    result = result + str[:scheme_end]
	    str = str[scheme_end:]
	# Find next string or Scheme expression:
	match = string_or_scheme.search (str)
    # Convert the remainder of the file
    result = result + articulation_substitute (str)
    return result

def conv_relative(str):
    if re.search (r"\\relative", str):
	str= "#(ly:set-option 'old-relative)\n" + str

    return str

@rule ((1, 9, 0), _ ("""New relative mode,
Postfix articulations, new text markup syntax, new chord syntax."""))
def conv (str):
    str = re.sub (r"#'\(\)", "@SCM_EOL@", str)
    str =  conv_relative (str)
    str = sub_chords (str)

    str = text_markup (str)
    str = smarter_articulation_subst (str)
    str = re.sub ("@SCM_EOL@", "#'()", str)
    return str


@rule ((1, 9, 1), _ ("Remove - before articulation"))
def conv (str):
    if re.search ("font-style",str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % "font-style")
	stderr_write ('\n')
	stderr_write (UPDATE_MANUALLY)
	stderr_write ('\n')

	raise FatalConversionError ()

    str = re.sub (r'-\\markup', r'@\\markup', str)
    str = re.sub (r'-\\', r'\\', str)
    str = re.sub (r'-\)', ')', str)
    str = re.sub (r'-\(', '(', str)
    str = re.sub ('-\[', '[', str)
    str = re.sub ('-\]', ']', str)
    str = re.sub ('-~', '~', str)
    str = re.sub (r'@\\markup', r'-\\markup', str)
    return str


@rule ((1, 9, 2), "\\newcontext -> \\new")
def conv (str):
    str = re.sub ('ly:set-context-property',
		  'ly:set-context-property!', str)
    str = re.sub ('\\\\newcontext', '\\\\new', str)
    str = re.sub ('\\\\grace[\t\n ]*([^{ ]+)',
		  r'\\grace { \1 }', str)
    str = re.sub ("\\\\grace[\t\n ]*{([^}]+)}",
		  r"""\\grace {
\\property Voice.Stem \\override #'stroke-style = #"grace"
  \1
  \\property Voice.Stem \\revert #'stroke-style }
""", str)
    return str


@rule ((1, 9, 3), (_ ("%s misspelling") % "\\acciaccatura") + 
                         ", fingerHorizontalDirection -> fingeringOrientations")
def conv (str):
    str = re.sub ('accacciatura',
		  'acciaccatura', str)

    if re.search ("context-spec-music", str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % "context-spec-music")
	stderr_write ('\n')
	stderr_write (UPDATE_MANUALLY)
	stderr_write ('\n')

	raise FatalConversionError ()

    str = re.sub ('fingerHorizontalDirection *= *#(LEFT|-1)',
		  "fingeringOrientations = #'(up down left)", str)
    str = re.sub ('fingerHorizontalDirection *= *#(RIGHT|1)',
		  "fingeringOrientations = #'(up down right)", str)
    return str


@rule ((1, 9, 4), _ ('Swap < > and << >>'))
def conv (str):
    if re.search ('\\figures', str):
	warning (_ ("attempting automatic \\figures conversion.  Check results!"));

    def figures_replace (m):
	s = m.group (1)
	s = re.sub ('<', '@FIGOPEN@',s)
	s = re.sub ('>', '@FIGCLOSE@',s)
	return '\\figures { %s }' % s

    str = re.sub (r'\\figures[ \t\n]*{([^}]+)}', figures_replace, str)
    str = re.sub (r'\\<', '@STARTCRESC@', str)
    str = re.sub (r'\\>', '@STARTDECRESC@', str)
    str = re.sub (r'([-^_])>', r'\1@ACCENT@', str)
    str = re.sub (r'<<', '@STARTCHORD@', str)
    str = re.sub (r'>>', '@ENDCHORD@', str)
    str = re.sub (r'>', '@ENDSIMUL@', str)
    str = re.sub (r'<', '@STARTSIMUL@', str)
    str = re.sub ('@STARTDECRESC@', '\\>', str)
    str = re.sub ('@STARTCRESC@', '\\<', str)
    str = re.sub ('@ACCENT@', '>', str)
    str = re.sub ('@ENDCHORD@', '>', str)
    str = re.sub ('@STARTCHORD@', '<', str)
    str = re.sub ('@STARTSIMUL@', '<<', str)
    str = re.sub ('@ENDSIMUL@', '>>', str)
    str = re.sub ('@FIGOPEN@', '<', str)
    str = re.sub ('@FIGCLOSE@', '>', str)
    return str


@rule ((1, 9, 5), 'HaraKiriVerticalGroup -> RemoveEmptyVerticalGroup')
def conv (str):
    str = re.sub ('HaraKiriVerticalGroup', 'RemoveEmptyVerticalGroup', str)
    return str


@rule ((1, 9, 6), _ ('deprecate %s') % 'ly:get-font')
def conv (str):
    if re.search ("ly:get-font", str) :
	stderr_write ('\n')
	stderr_write (NOT_SMART % "(ly:-get-font")
	stderr_write ('\n')
	stderr_write (FROM_TO \
			  % ("(ly:paper-get-font (ly:grob-get-paper foo) .. )",
			     "(ly:paper-get-font (ly:grob-get-paper foo) .. )"))
	stderr_write (UPDATE_MANUALLY)
	stderr_write ('\n')
	raise FatalConversionError ()

    if re.search ("\\pitch *#", str) :
	stderr_write ('\n')
	stderr_write (NOT_SMART % "\\pitch")
	stderr_write ('\n')
	stderr_write (_ ("Use Scheme code to construct arbitrary note events."))
	stderr_write ('\n')

	raise FatalConversionError ()
    return str


@rule ((1, 9, 7), _ ('''use symbolic constants for alterations,
remove \\outputproperty, move ly:verbose into ly:get-option'''))
def conv (str):
    def sub_alteration (m):
	alt = m.group (3)
	alt = {
		'-1': 'FLAT',
		'-2': 'DOUBLE-FLAT',
		'0': 'NATURAL',
		'1': 'SHARP',
		'2': 'DOUBLE-SHARP',
		}[alt]

	return '(ly:make-pitch %s %s %s)' % (m.group(1), m.group (2),
					     alt)

    str =re.sub ("\\(ly:make-pitch *([0-9-]+) *([0-9-]+) *([0-9-]+) *\\)",
		 sub_alteration, str)


    str = re.sub ("ly:verbose", "ly:get-option 'verbose", str)

    m= re.search ("\\\\outputproperty #([^#]+)[\t\n ]*#'([^ ]+)", str)
    if m:
	stderr_write (_ (\
		r"""\outputproperty found,
Please hand-edit, using

  \applyoutput #(outputproperty-compatibility %s '%s <GROB PROPERTY VALUE>)

as a substitution text.""") % (m.group (1), m.group (2)) )
	raise FatalConversionError ()

    if re.search ("ly:(make-pitch|pitch-alteration)", str) \
	   or re.search ("keySignature", str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % "pitches")
	stderr_write ('\n')
	stderr_write (
	    _ ("""The alteration field of Scheme pitches was multiplied by 2
to support quarter tone accidentals.  You must update the following constructs manually:

* calls of ly:make-pitch and ly:pitch-alteration
* keySignature settings made with \property
"""))
	raise FatalConversionError ()
    return str


@rule ((1, 9, 8), "dash-length -> dash-fraction")
def conv (str):
    if re.search ("dash-length",str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % "dash-length")
	stderr_write ('\n')
	stderr_write (FROM_TO % ("dash-length", "dash-fraction"))
	stderr_write ('\n')
	stderr_write (UPDATE_MANUALLY)
	stderr_write ('\n')
	raise FatalConversionError ()
    return str


@rule ((2, 1, 1), "font-relative-size -> font-size")
def conv (str):
    def func(match):
	return "#'font-size = #%d" % (2*int (match.group (1)))

    str =re.sub (r"#'font-relative-size\s*=\s*#\+?([0-9-]+)", func, str)
    str =re.sub (r"#'font-family\s*=\s*#'ancient",
		 r"#'font-family = #'music", str)
    return str


@rule ((2, 1, 2), "ly:get-music-length -> ly:music-length")
def conv (str):
    str =re.sub (r"ly:get-music-length", "ly:music-length", str)
    return str


@rule ((2, 1, 3), "stanza -> instrument")
def conv (str):
    str =re.sub (r"\.\s+stz=", ". instr ", str)
    return str


@rule ((2, 1, 4), _ ("removal of automaticMelismata; use melismaBusyProperties instead."))
def conv (str):
    def func (match):
	c = match.group (1)
	b = match.group (2)

	if b == 't':
	    if c == 'Score':
		return ''
	    else:
		return r" \property %s.melismaBusyProperties \unset"  % c
	elif b == 'f':
	    return r"\property %s.melismaBusyProperties = #'(melismaBusy)"  % c

    str = re.sub (r"\\property ([a-zA-Z]+)\s*\.\s*automaticMelismata\s*=\s*##([ft])", func, str)
    return str


@rule ((2, 1, 7), "\\translator Staff -> \\change Staff")
def conv (str):
    str =re.sub (r"\\translator\s+([a-zA-Z]+)", r"\\change \1", str)
    return str


@rule ((2, 1, 10), "\\newaddlyrics -> \\lyricsto")
def conv (str):
    str =re.sub (r"\\newaddlyrics", r"\\lyricsto", str)
    return str


@rule ((2, 1, 11), """\\include "paper16.ly" -> #(set-staff-size 16)
\\note #3 #1 #1 -> \\note #"8." #1
""")
def conv (str):
    str = re.sub (r'\\include\s*"paper([0-9]+)(-init)?.ly"',
		  r"#(set-staff-size \1)", str)

    def sub_note (match):
	dur = ''
	log = int (match.group (1))
	dots = int (match.group (2))

	if log >= 0:
	    dur = '%d' % (1 << log)
	else:
	    dur = { -1 : 'breve',
		    -2 : 'longa',
		    -3 : 'maxima'}[log]

	dur += ('.' * dots)

	return r'\note #"%s" #%s' % (dur, match.group (3))

    str = re.sub (r'\\note\s+#([0-9-]+)\s+#([0-9]+)\s+#([0-9.-]+)',
		  sub_note, str)
    return str


@rule ((2, 1, 12), "OttavaSpanner -> OttavaBracket")
def conv (str):
    str = re.sub (r"OttavaSpanner", r"OttavaBracket", str)
    return str


@rule ((2, 1, 13), "set-staff-size -> set-global-staff-size")
def conv (str):
    str = re.sub (r"\(set-staff-size ", r"(set-global-staff-size ", str)
    return str


@rule ((2, 1, 14), "style = dotted -> dash-fraction = 0")
def conv (str):
    str = re.sub (r"#'style\s*=\s*#'dotted-line",
		 r"#'dash-fraction = #0.0 ", str)
    return str


@rule ((2, 1, 15), "LyricsVoice . instr(ument) -> vocalName")
def conv (str):
    str = re.sub (r'LyricsVoice\s*\.\s*instrument\s*=\s*("[^"]*")',
		 r'LyricsVoice . vocalName = \1', str)

    str = re.sub (r'LyricsVoice\s*\.\s*instr\s*=\s*("[^"]*")',
		 r'LyricsVoice . vocNam = \1', str)
    return str


@rule ((2, 1, 16), '\\musicglyph #"accidentals-NUM" -> \\sharp/flat/etc.')
def conv (str):
    def sub_acc (m):
	d = {
	'4': 'doublesharp',
	'3': 'threeqsharp',
	'2': 'sharp',
	'1': 'semisharp',
	'0': 'natural',
	'-1': 'semiflat',
	'-2': 'flat',
	'-3': 'threeqflat',
	'-4': 'doubleflat'}
	return '\\%s' %  d[m.group (1)]

    str = re.sub (r'\\musicglyph\s*#"accidentals-([0-9-]+)"',
		  sub_acc, str)
    return str


@rule ((2, 1, 17), _ ("\\partcombine syntax change to \\newpartcombine"))
def conv (str):

    if re.search (r'\\partcombine', str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % "\\partcombine")
	stderr_write ('\n')
	stderr_write (UPDATE_MANUALLY)
	stderr_write ('\n')
	raise FatalConversionError ()

    # this rule doesn't really work,
    # too lazy to figure out why.
    str = re.sub (r'\\context\s+Voice\s*=\s*one\s*\\partcombine\s+Voice\s*\\context\s+Thread\s*=\s*one(.*)\s*'
		  + r'\\context\s+Thread\s*=\s*two',
		  '\\\\newpartcombine\n\\1\n', str)
    return str


@rule ((2, 1, 18), """\\newpartcombine -> \\partcombine,
\\autochange Staff -> \\autochange
""")
def conv (str):
    str = re.sub (r'\\newpartcombine', r'\\partcombine', str)
    str = re.sub (r'\\autochange\s+Staff', r'\\autochange ', str)
    return str


@rule ((2, 1, 19), _ ("""Drum notation changes, Removing \\chordmodifiers, \\notenames.
Harmonic notes. Thread context removed. Lyrics context removed."""))
def conv (str):
    if re.search ('include "drumpitch', str):
	stderr_write (_ ("Drums found. Enclose drum notes in \\drummode"))

    str = re.sub (r'\\include "drumpitch-init.ly"','', str)

    str = re.sub (r'\\pitchnames ','pitchnames = ', str)
    str = re.sub (r'\\chordmodifiers ','chordmodifiers = ', str)
    str = re.sub (r'\bdrums\b\s*=','drumContents = ', str)
    str = re.sub (r'\\drums\b','\\drumContents ', str)


    if re.search ('drums->paper', str):
	stderr_write (_ ("\n%s found. Check file manually!\n") % _("Drum notation"))

    str = re.sub (r"""\\apply\s+#\(drums->paper\s+'([a-z]+)\)""",
		  r"""\property DrumStaff.drumStyleTable = #\1-style""",
		  str)

    if re.search ('Thread', str):
	stderr_write (_ ("\n%s found. Check file manually!\n") % "Thread");

    str = re.sub (r"""(\\once\s*)?\\property\s+Thread\s*\.\s*NoteHead\s*"""
		  + r"""\\(set|override)\s*#'style\s*=\s*#'harmonic"""
		  + r"""\s+([a-z]+[,'=]*)([0-9]*\.*)"""
		  ,r"""<\3\\harmonic>\4""", str)

    str = re.sub (r"""\\new Thread""", """\context Voice""", str)
    str = re.sub (r"""Thread""", """Voice""", str)

    if re.search ('\bLyrics\b', str):
	stderr_write (_ ("\n%s found. Check file manually!\n") % "Lyrics");

    str = re.sub (r"""LyricsVoice""", r"""L@ricsVoice""", str)
    str = re.sub (r"""\bLyrics\b""", r"""LyricsVoice""", str)
    str = re.sub (r"""LyricsContext""", r"""LyricsVoiceContext""", str)
    str = re.sub (r"""L@ricsVoice""", r"""LyricsVoice""",str)
    return str


@rule ((2, 1, 20), "nonevent-skip -> skip-music")
def conv (str):
    str = re.sub (r'nonevent-skip', 'skip-music', str)
    return str


@rule ((2, 1, 21), """molecule-callback -> print-function,
brew_molecule -> print
brew-new-markup-molecule -> Text_item::print
LyricsVoice -> Lyrics
tupletInvisible -> TupletBracket \set #'transparent
%s.
""" % (_ ("remove %s") % "Grob::preset_extent"))
def conv (str):
    str = re.sub (r'molecule-callback', 'print-function', str)
    str = re.sub (r'brew_molecule', 'print', str)
    str = re.sub (r'brew-new-markup-molecule', 'Text_item::print', str)
    str = re.sub (r'LyricsVoice', 'Lyrics', str)
    str = re.sub (r'tupletInvisible',
		  r"TupletBracket \\set #'transparent", str)
#	str = re.sub (r'molecule', 'collage', str)
#molecule -> collage
    str = re.sub (r"\\property\s+[a-zA-Z]+\s*\.\s*[a-zA-Z]+\s*"
		  + r"\\set\s*#'X-extent-callback\s*=\s*#Grob::preset_extent",
		  "", str)
    return str


@rule ((2, 1, 22), """%s
        \\set A.B = #C , \\unset A.B
        \\override A.B #C = #D, \\revert A.B #C

""" % _ ("new syntax for property settings:"))
def conv (str):
    str = re.sub (r'(\\property[^=]+)=\s*([-0-9]+)',
		  r'\1= #\2', str)
    str = re.sub (r'\\property\s+([^. ]+)\s*\.\s*([^\\=]+)\s*\\(set|override)',
		  r"\\overrid@ \1.\2 ", str)
    str = re.sub (r'\\property\s+([^. ]+)\s*\.\s*([^\\= ]+)\s*=\s*',
		  r'\\s@t \1.\2 = ', str)
    str = re.sub (r'\\property\s+([^. ]+)\s*\.\s*([^\\= ]+)\s*\\unset',
		  r'\\uns@t \1.\2 ', str)
    str = re.sub (r'\\property\s+([^. ]+)\s*\.\s*([^\\= ]+)\s*\\revert'
		  + r"\s*#'([-a-z0-9_]+)",
		  r"\\rev@rt \1.\2 #'\3", str)
    str = re.sub (r'Voice\.', '', str)
    str = re.sub (r'Lyrics\.', '', str)
    str = re.sub (r'ChordNames\.', '', str)

    str = re.sub ('rev@rt', 'revert',str)
    str = re.sub ('s@t', 'set',str)
    str = re.sub ('overrid@', 'override',str)

    str = re.sub ('molecule', 'stencil', str)
    str = re.sub ('Molecule', 'Stencil', str)
    return str


@rule ((2, 1, 23), _ ("Property setting syntax in \\translator{ }"))
def conv (str):
    def subst_in_trans (match):
	s = match.group (0)
	s = re.sub (r'\s([a-zA-Z]+)\s*\\override',
		      r' \\override \1', s)
	s = re.sub (r'\s([a-zA-Z]+)\s*\\set',
		      r' \\override \1', s)
	s = re.sub (r'\s([a-zA-Z]+)\s*\\revert',
		      r' \\revert \1', s)
	return s
    str = re.sub (r'\\(translator|with)\s*{[^}]+}',  subst_in_trans, str)

    def sub_abs (m):

	context = m.group ('context')
	d = m.groupdict ()
	if context:
	    context = " '%s" % context[:-1] # -1: remove .
	else:
	    context = ''

	d['context'] = context

	return r"""#(override-auto-beam-setting %(prop)s %(num)s %(den)s%(context)s)""" % d

    str = re.sub (r"""\\override\s*(?P<context>[a-zA-Z]+\s*\.\s*)?autoBeamSettings"""
		  +r"""\s*#(?P<prop>[^=]+)\s*=\s*#\(ly:make-moment\s+(?P<num>\d+)\s+(?P<den>\d)\s*\)""",
		  sub_abs, str)
    return str


@rule ((2, 1, 24), "music-list? -> ly:music-list?")
def conv (str):
    str = re.sub (r'music-list\?', 'ly:music-list?', str)
    str = re.sub (r'\|\s*~', '~ |', str)
    return str


@rule ((2, 1, 25), _ ("Scheme grob function renaming"))
def conv (str):
    str = re.sub (r'ly:get-spanner-bound', 'ly:spanner-get-bound', str)
    str = re.sub (r'ly:get-extent', 'ly:grob-extent', str)
    str = re.sub (r'ly:get-system', 'ly:grob-system', str)
    str = re.sub (r'ly:get-original', 'ly:grob-original', str)
    str = re.sub (r'ly:get-parent', 'ly:grob-parent', str)
    str = re.sub (r'ly:get-broken-into', 'ly:spanner-broken-into', str)
    str = re.sub (r'Melisma_engraver', 'Melisma_translator', str)
    if re.search ("ly:get-paper-variable", str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % "ly:paper-get-variable")
	stderr_write ('\n')
	stderr_write (_ ('use %s') % '(ly:paper-lookup (ly:grob-paper ))')
	stderr_write ('\n')
	raise FatalConversionError ()

    str = re.sub (r'\\defaultAccidentals', "#(set-accidental-style 'default)", str)
    str = re.sub (r'\\voiceAccidentals', "#(set-accidental-style 'voice)", str)
    str = re.sub (r'\\modernAccidentals', "#(set-accidental-style 'modern)", str)
    str = re.sub (r'\\modernCautionaries', "#(set-accidental-style 'modern-cautionary)", str)
    str = re.sub (r'\\modernVoiceAccidental', "#(set-accidental-style 'modern-voice)", str)
    str = re.sub (r'\\modernVoiceCautionaries', "#(set-accidental-style 'modern-voice-cautionary)", str)
    str = re.sub (r'\\pianoAccidentals', "#(set-accidental-style 'piano)", str)
    str = re.sub (r'\\pianoCautionaries', "#(set-accidental-style 'piano-cautionary)", str)
    str = re.sub (r'\\forgetAccidentals', "#(set-accidental-style 'forget)", str)
    str = re.sub (r'\\noResetKey', "#(set-accidental-style 'no-reset)", str)
    return str


@rule ((2, 1, 26), _ ("More Scheme function renaming"))
def conv (str):
    str = re.sub ('ly:set-grob-property!', 'ly:grob-set-property!',str)
    str = re.sub ('ly:set-mus-property!', 'ly:music-set-property!',str)
    str = re.sub ('ly:set-context-property!', 'ly:context-set-property!', str)
    str = re.sub ('ly:get-grob-property', 'ly:grob-property',str)
    str = re.sub ('ly:get-mus-property', 'ly:music-property',str)
    str = re.sub ('ly:get-context-property', 'ly:context-property',str)
    return str


@rule ((2, 1, 27), "property transposing -> tuning")
def conv (str):
    def subst (m):
	g = int (m.group (2))
	o = g / 12
	g -= o * 12
	if g <  0:
	    g += 12
	    o -= 1


	lower_pitches = filter (lambda x : x <= g, [0, 2, 4, 5, 7, 9, 11, 12])
	s = len (lower_pitches) -1
	a = g - lower_pitches [-1]


	print s , lower_pitches, g, a, s
	str = 'cdefgab' [s]
	str += ['eses', 'es', '', 'is', 'isis'][a + 2]
	if o < 0:
	    str += ',' * (-o - 1)
	elif o >= 0:
	    str += "'" * (o + 1)

	return '\\transposition %s ' % str


    str = re.sub (r"\\set ([A-Za-z]+\s*\.\s*)?transposing\s*=\s*#([-0-9]+)",
		  subst, str)
    return str


@rule ((2, 1, 28), """make-music-by-name -> make-music,
new syntax for setting \\arpeggioBracket""")
def conv (str):
    str = re.sub (r'make-music-by-name', 'make-music', str)
    str = re.sub (r"\\override\s+.*Arpeggio\s+#.print-function\s+=\s+\\arpeggioBracket", r"\\arpeggioBracket", str)
    return str


@rule ((2, 1, 29), '\\center -> \\center-align, \\translator -> \\context')
def conv (str):
    str = re.sub (r'\\center([^-])', '\\center-align\\1', str)
    str = re.sub (r'\\translator', '\\context', str)
    return str


@rule ((2, 1, 30), '''\\threeq{flat,sharp} -> \\sesqui{flat,sharp}
ly:get-mutable-properties -> ly:mutable-music-properties
centralCPosition -> middleCPosition
ly:unset-context-property -> ly:context-unset-property
ly:translator-find -> ly:context-find
ly:get-stencil-extent -> ly:stencil-extent
''')
def conv (str):
    str = re.sub (r'\\threeq(flat|sharp)', r'\\sesqui\1', str)
    str = re.sub (r'ly:stencil-get-extent',
		  'ly:stencil-extent', str)
    str = re.sub (r'ly:translator-find',
		  'ly:context-find', str)
    str = re.sub ('ly:unset-context-property','ly:context-unset-property',
		  str)

    str = re.sub (r'ly:get-mutable-properties',
		  'ly:mutable-music-properties',str)
    str = re.sub (r'centralCPosition',
		  'middleCPosition',str)
    return str


@rule ((2, 1, 31), 'remove \\alias Timing')
def conv (str):
    str = re.sub (r'\\alias\s*"?Timing"?', '', str)
    return str


@rule ((2, 1, 33), 'breakAlignOrder -> break-align-orders.')
def conv (str):
    str = re.sub (r"(\\set\s+)?(?P<context>(Score\.)?)breakAlignOrder\s*=\s*#'(?P<list>[^\)]+)",
		  r"\n\\override \g<context>BreakAlignment #'break-align-orders = "
		  + "#(make-vector 3 '\g<list>)", str)
    return str


@rule ((2, 1, 34), 'set-paper-size -> set-default-paper-size.')
def conv (str):
    str = re.sub (r"\(set-paper-size",
		  "(set-default-paper-size",str)
    return str


@rule ((2, 1, 36), 'ly:mutable-music-properties -> ly:music-mutable-properties')
def conv (str):
    str = re.sub (r"ly:mutable-music-properties",
		  "ly:music-mutable-properties", str)
    return str


@rule ((2, 2, 0), _ ("bump version for release"))
def conv (str):
    return str


@rule ((2, 3, 1), '\\apply -> \\applymusic')
def conv (str):
    return re.sub (r'\\apply\b', r'\\applymusic', str)


@rule ((2, 3, 2), '\\FooContext -> \\Foo')
def conv (str):
    if re.search ('textheight', str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % "textheight")
	stderr_write ('\n')
	stderr_write (UPDATE_MANUALLY)
	stderr_write ('\n')
	stderr_write (
_ ("""Page layout has been changed, using paper size and margins.
textheight is no longer used.
"""))
    str = re.sub (r'\\OrchestralScoreContext', '\\Score', str)
    def func(m):
	if m.group(1) not in ['RemoveEmptyStaff',
			      'AncientRemoveEmptyStaffContext',
			      'EasyNotation']:
	    return '\\' + m.group (1)
	else:
	    return m.group (0)


    str = re.sub (r'\\([a-zA-Z]+)Context\b', func, str)
    str = re.sub ('ly:paper-lookup', 'ly:output-def-lookup', str)
    return str


@rule ((2, 3, 4), _ ('remove %s') % '\\notes')
def conv (str):
    str = re.sub (r'\\notes\b', '', str)
    return str


@rule ((2, 3, 6), 'lastpagefill -> raggedlastbottom')
def conv (str):
    str = re.sub (r'lastpagefill\s*=\s*"?1"', 'raggedlastbottom = ##t', str)
    return str


@rule ((2, 3, 8), 'remove \\consistsend, strip \\lyrics from \\lyricsto.')
def conv (str):
    str = re.sub (r'\\consistsend', '\\consists', str)
    str = re.sub (r'\\lyricsto\s+("?[a-zA-Z]+"?)(\s*\\new Lyrics\s*)?\\lyrics',
		  r'\\lyricsto \1 \2', str)
    return str


@rule ((2, 3, 9), 'neo_mensural -> neomensural, if-text-padding -> bound-padding')
def conv (str):
    str = re.sub (r'neo_mensural', 'neomensural', str)
    str = re.sub (r'if-text-padding', 'bound-padding', str)
    return str


@rule ((2, 3, 10), '\\addlyrics -> \\oldaddlyrics, \\newlyrics -> \\addlyrics')
def conv (str):
    str = re.sub (r'\\addlyrics', r'\\oldaddlyrics', str)
    str = re.sub (r'\\newlyrics', r'\\addlyrics', str)
    if re.search (r"\\override\s*TextSpanner", str):
	stderr_write ("\nWarning: TextSpanner has been split into DynamicTextSpanner and TextSpanner\n")
    return str


@rule ((2, 3, 11), '\\setMmRestFermata -> ^\\fermataMarkup')
def conv (str):
    str = re.sub (r'\\setMmRestFermata\s+(R[0-9.*/]*)',
		  r'\1^\\fermataMarkup', str)
    return str


@rule ((2, 3, 12), '''\\newpage -> \\pageBreak, junk \\script{up,down,both},
soloADue -> printPartCombineTexts, #notes-to-clusters -> \\makeClusters
''')
def conv (str):
    str = re.sub (r'\\newpage', r'\\pageBreak', str)
    str = re.sub (r'\\scriptUp', r"""{
\\override TextScript  #'direction = #1
\\override Script  #'direction = #1
}""", str)
    str = re.sub (r'\\scriptDown', r"""{
  \\override TextScript  #'direction = #-1
  \\override Script  #'direction = #-1
}""", str)
    str = re.sub (r'\\scriptBoth', r"""{
  \\revert TextScript  #'direction
  \\revert Script  #'direction
}""", str)
    str = re.sub ('soloADue', 'printPartCombineTexts', str)
    str = re.sub (r'\\applymusic\s*#notes-to-clusters',
		      '\\makeClusters', str)
    
    str = re.sub (r'pagenumber\s*=', 'firstpagenumber = ', str)
    return str


@rule ((2, 3, 16), _ ('''\\foo -> \\foomode (for chords, notes, etc.)
fold \\new FooContext \\foomode into \\foo.'''))
def conv (str):
    str = re.sub (r'\\chords\b', r'\\chordmode', str)
    str = re.sub (r'\\lyrics\b', r'\\lyricmode', str)
    str = re.sub (r'\\figures\b', r'\\figuremode', str)
    str = re.sub (r'\\notes\b', r'\\notemode', str)
    str = re.sub (r'\\drums\b', r'\\drummode', str)
    str = re.sub (r'\\chordmode\s*\\new ChordNames', r'\\chords', str)
    str = re.sub (r'\\new ChordNames\s*\\chordmode', r'\\chords', str)
    str = re.sub (r'\\new FiguredBass\s*\\figuremode', r'\\figures', str)
    str = re.sub (r'\\figuremode\s*\new FiguredBass', r'\\figures', str)
    str = re.sub (r'\\new DrumStaff\s*\\drummode', r'\\drums', str)
    str = re.sub (r'\\drummode\s*\\new DrumStaff', r'\\drums', str)

    return str


@rule ((2, 3, 17), '''slurBoth -> slurNeutral, stemBoth -> stemNeutral, etc.
\\applymusic #(remove-tag 'foo) -> \\removeWithTag 'foo''')
def conv (str):
    str = re.sub (r'(slur|stem|phrasingSlur|tie|dynamic|dots|tuplet|arpeggio|)Both', r'\1Neutral', str)
    str = re.sub (r"\\applymusic\s*#\(remove-tag\s*'([a-z-0-9]+)\)",
		  r"\\removeWithTag #'\1", str)
    return str


@rule ((2, 3, 18), 'Text_item -> Text_interface')
def conv (str):
    str = re.sub (r'Text_item', 'Text_interface', str)
    return str


@rule ((2, 3, 22), 'paper -> layout, bookpaper -> paper')
def conv (str):
    str = re.sub (r'\\paper', r'\\layout', str)
    str = re.sub (r'\\bookpaper', r'\\paper', str)
    if re.search ('paper-set-staff-size', str):
	warning (_ ('''staff size should be changed at top-level
with

  #(set-global-staff-size <STAFF-HEIGHT-IN-POINT>)

'''))


    str = re.sub (r'#\(paper-set-staff-size', '%Use set-global-staff-size at toplevel\n% #(layout-set-staff-size', str)
    return str
    

@rule ((2, 3, 23), r'\context Foo = NOTENAME -> \context Foo = "NOTENAME"')
def conv (str):
    str = re.sub (r'\\context\s+([a-zA-Z]+)\s*=\s*([a-z]+)\s',
		  r'\\context \1 = "\2" ',
		  str )
    return str


@rule ((2, 3, 24), _ ('''regularize other identifiers'''))
def conv (str):
    def sub(m):
	return regularize_id (m.group (1))
    str = re.sub (r'(maintainer_email|maintainer_web|midi_stuff|gourlay_maxmeasures)',
		  sub, str)
    return str


@rule ((2, 3, 25), 'petrucci_c1 -> petrucci-c1, 1style -> single-digit')
def conv (str):
    str = re.sub ('petrucci_c1', 'petrucci-c1', str)
    str = re.sub ('1style', 'single-digit', str)
    return str


@rule ((2, 4, 0), _ ("bump version for release"))
def conv (str):
    return str


@rule ((2, 5, 0), '\\quote -> \\quoteDuring')
def conv (str):
    str = re.sub (r'\\quote\s+"?([a-zA-Z0-9]+)"?\s+([0-9.*/]+)',
		  r'\\quoteDuring #"\1" { \skip \2 }',
		  str)
    return str


@rule ((2, 5, 1), 'ly:import-module -> ly:module-copy')
def conv (str):
    str = re.sub (r'ly:import-module',
		  r'ly:module-copy', str)
    return str


@rule ((2, 5, 2), '\markup .. < .. > .. -> \markup .. { .. } ..')
def conv (str):
    str = re.sub (r'\\(column|fill-line|dir-column|center-align|right-align|left-align|bracketed-y-column)\s*<(([^>]|<[^>]*>)*)>',
		  r'\\\1 {\2}', str)
    str = re.sub (r'\\(column|fill-line|dir-column|center-align|right-align|left-align|bracketed-y-column)\s*<(([^>]|<[^>]*>)*)>',
		  r'\\\1 {\2}', str)
    str = re.sub (r'\\(column|fill-line|dir-column|center-align|right-align|left-align|bracketed-y-column)\s*<(([^>]|<[^>]*>)*)>',
		  r'\\\1 {\2}', str)
    def get_markup (m):
	s = m.group (0)
	s = re.sub (r'''((\\"|})\s*){''', '\2 \\line {', s)
	return s
    str = re.sub (r'\\markup\s*{([^}]|{[^}]*})*}', get_markup, str)
    return str


@rule ((2, 5, 3), 'ly:find-glyph-by-name -> ly:font-get-glyph, remove - from glyphnames.')
def conv (str):
    str = re.sub ('ly:find-glyph-by-name', 'ly:font-get-glyph', str)
    str = re.sub ('"(scripts|clefs|accidentals)-', r'"\1.', str)
    str = re.sub ("'hufnagel-do-fa", "'hufnagel.do.fa", str)
    str = re.sub ("'(vaticana|hufnagel|medicaea|petrucci|neomensural|mensural)-", r"'\1.", str)
    return str


@rule ((2, 5, 12), '\set Slur #\'dashed = #X -> \slurDashed')
def conv (str):
    str = re.sub (r"\\override\s+(Voice\.)?Slur #'dashed\s*=\s*#\d*(\.\d+)?",
		  r"\\slurDashed", str)
    return str


@rule ((2, 5, 13), _ ('\\encoding: smart recode latin1..utf-8. Remove ly:point-and-click'))
def conv (str):
    input_encoding = 'latin1'
    def func (match):
	encoding = match.group (1)

	# FIXME: automatic recoding of other than latin1?
	if encoding == 'latin1':
	    return match.group (2)

	stderr_write ('\n')
	stderr_write (NOT_SMART % ("\\encoding: %s" % encoding))
	stderr_write ('\n')
	stderr_write (_ ("LilyPond source must be UTF-8"))
	stderr_write ('\n')
	if encoding == 'TeX':
	    stderr_write (_ ("Try the texstrings backend"))
	    stderr_write ('\n')
	else:
	    stderr_write ( _("Do something like: %s") % \
			       ("recode %s..utf-8 FILE" % encoding))
	    stderr_write ('\n')
	stderr_write (_ ("Or save as UTF-8 in your editor"))
	stderr_write ('\n')
	raise FatalConversionError ()

	return match.group (0)

    str = re.sub (r'\\encoding\s+"?([a-zA-Z0-9]+)"?(\s+)', func, str)

    import codecs
    de_ascii = codecs.getdecoder ('ascii')
    de_utf_8 = codecs.getdecoder ('utf_8')
    de_input = codecs.getdecoder (input_encoding)
    en_utf_8 = codecs.getencoder ('utf_8')
    try:
	de_ascii (str)
    # only in python >= 2.3
    # except UnicodeDecodeError:
    except UnicodeError:
	# do not re-recode UTF-8 input
	try:
	    de_utf_8 (str)
	#except UnicodeDecodeError:
	except UnicodeError:
	    str = en_utf_8 (de_input (str)[0])[0]



    str = re.sub (r"#\(ly:set-point-and-click '[a-z-]+\)", '', str)
    return str


@rule ((2, 5, 17), _ ('remove %s') % 'ly:stencil-set-extent!')
def conv (str):
    if re.search ("ly:stencil-set-extent!", str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % "ly:stencil-set-extent!")
	stderr_write ('\n')
	stderr_write ('use (set! VAR (ly:make-stencil (ly:stencil-expr VAR) X-EXT Y-EXT))\n')
	raise FatalConversionError ()
    if re.search ("ly:stencil-align-to!", str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % "ly:stencil-align-to!")
	stderr_write ('\n')
	stderr_write ('use (set! VAR (ly:stencil-aligned-to VAR AXIS DIR))\n')
	raise FatalConversionError ()
    return str


@rule ((2, 5, 18), 'ly:warn -> ly:warning')
def conv (str):
    str = re.sub (r"ly:warn\b", 'ly:warning', str)
    return str


@rule ((2, 5, 21), _ ('warn about auto beam settings'))
def conv (str):
    if re.search ("(override-|revert-)auto-beam-setting", str)\
       or re.search ("autoBeamSettings", str):
	stderr_write ('\n')
	stderr_write (NOT_SMART % _ ("auto beam settings"))
	stderr_write ('\n')
	stderr_write (_ ('''
Auto beam settings must now specify each interesting moment in a measure
explicitely; 1/4 is no longer multiplied to cover moments 1/2 and 3/4 too.
'''))
	stderr_write (UPDATE_MANUALLY)
	stderr_write ('\n')
	raise FatalConversionError ()
    return str


@rule ((2, 5, 25), 'unfoldrepeats -> unfoldRepeats, compressmusic -> compressMusic')
def conv (str):
    str = re.sub (r"unfoldrepeats", 'unfoldRepeats', str)
    str = re.sub (r"compressmusic", 'compressMusic', str)
    return str


@rule ((2, 6, 0), _ ("bump version for release"))
def conv (str):
    return str


@rule ((2, 7, 0), 'ly:get-default-font -> ly:grob-default-font')
def conv (str):
    return re.sub('ly:get-default-font', 'ly:grob-default-font', str) 


@rule ((2, 7, 1), '''ly:parser-define -> ly:parser-define!
excentricity -> eccentricity
Timing_engraver -> Timing_translator + Default_bar_line_engraver
''')
def conv (str):
    str = re.sub('ly:parser-define', 'ly:parser-define!', str)
    str = re.sub('excentricity', 'eccentricity', str)
    str = re.sub(r'\\(consists|remove) *"?Timing_engraver"?',
		 r'\\\1 "Timing_translator" \\\1 "Default_bar_line_engraver"',
		 str)
    return str


@rule ((2, 7, 2), 'ly:X-moment -> ly:moment-X')
def conv (str):
    str = re.sub('ly:(add|mul|mod|div)-moment', r'ly:moment-\1', str)
    return str


@rule ((2, 7, 4), 'keyAccidentalOrder -> keyAlterationOrder')
def conv (str):
    str = re.sub('keyAccidentalOrder', 'keyAlterationOrder', str)
    return str


@rule ((2, 7, 6), '''Performer_group_performer -> Performer_group, Engraver_group_engraver -> Engraver_group,
inside-slur -> avoid-slur''')
def conv (str):
    str = re.sub('Performer_group_performer', 'Performer_group', str)
    str = re.sub('Engraver_group_engraver', 'Engraver_group', str)
    str = re.sub (r"#'inside-slur\s*=\s*##t *",
		  r"#'avoid-slur = #'inside ", str)
    str = re.sub (r"#'inside-slur\s*=\s*##f *",
		  r"#'avoid-slur = #'around ", str)
    str = re.sub (r"#'inside-slur",
		  r"#'avoid-slur", str)
    return str


@rule ((2, 7, 10), '\\applyxxx -> \\applyXxx')
def conv (str):
    str = re.sub(r'\\applyoutput', r'\\applyOutput', str)
    str = re.sub(r'\\applycontext', r'\\applyContext', str)
    str = re.sub(r'\\applymusic',  r'\\applyMusic', str)
    str = re.sub(r'ly:grob-suicide', 'ly:grob-suicide!', str)
    return str


@rule ((2, 7, 11), '"tabloid" -> "11x17"')
def conv (str):
    str = re.sub(r'\"tabloid\"', '"11x17"', str)
    return str


@rule ((2, 7, 12), 'outputProperty -> overrideProperty')
def conv (str):
    str = re.sub(r'outputProperty' , 'overrideProperty', str)
    return str


@rule ((2, 7, 13), 'layout engine refactoring [FIXME]')
def conv (str):
    def subber (match):
	newkey = {'spacing-procedure': 'springs-and-rods',
		  'after-line-breaking-callback' : 'after-line-breaking',
		  'before-line-breaking-callback' : 'before-line-breaking',
		  'print-function' : 'stencil'} [match.group(3)]
	what = match.group (1)
	grob = match.group (2)

	if what == 'revert':
	    return "revert %s #'callbacks %% %s\n" % (grob, newkey)
	elif what == 'override':
	    return "override %s #'callbacks #'%s" % (grob, newkey)
	else:
	    raise 'urg'
	    return ''

    str = re.sub(r"(override|revert)\s*([a-zA-Z.]+)\s*#'(spacing-procedure|after-line-breaking-callback"
		+ r"|before-line-breaking-callback|print-function)",
		subber, str)

    if re.search ('bar-size-procedure', str):
	stderr_write (NOT_SMART % "bar-size-procedure")
    if re.search ('space-function', str):
	stderr_write (NOT_SMART % "space-function")
    if re.search ('verticalAlignmentChildCallback', str):
	stderr_write (_ ('verticalAlignmentChildCallback has been deprecated'))
    return str


@rule ((2, 7, 14), _ ('Remove callbacks property, deprecate XY-extent-callback.'))
def conv (str):
    str = re.sub (r"\\override +([A-Z.a-z]+) #'callbacks",
		  r"\\override \1", str)
    str = re.sub (r"\\revert ([A-Z.a-z]+) #'callbacks % ([a-zA-Z]+)",
		  r"\\revert \1 #'\2", str)
    str = re.sub (r"([XY]-extent)-callback", r'\1', str)
    str = re.sub (r"RemoveEmptyVerticalGroup", "VerticalAxisGroup", str)
    str = re.sub (r"\\set ([a-zA-Z]*\.?)minimumVerticalExtent",
		  r"\\override \1VerticalAxisGroup #'minimum-Y-extent",
		  str)
    str = re.sub (r"minimumVerticalExtent",
		  r"\\override VerticalAxisGroup #'minimum-Y-extent",
		  str)
    str = re.sub (r"\\set ([a-zA-Z]*\.?)extraVerticalExtent",
		  r"\\override \1VerticalAxisGroup #'extra-Y-extent", str)
    str = re.sub (r"\\set ([a-zA-Z]*\.?)verticalExtent",
		  r"\\override \1VerticalAxisGroup #'Y-extent", str)
    return str


@rule ((2, 7, 15), _ ('Use grob closures iso. XY-offset-callbacks.'))
def conv (str):
    if re.search ('[XY]-offset-callbacks', str):
	stderr_write (NOT_SMART % "[XY]-offset-callbacks")
    if re.search ('position-callbacks', str):
	stderr_write (NOT_SMART % "position-callbacks")
    return str


@rule ((2, 7, 22), r"\tag #'(a b) -> \tag #'a \tag #'b")
def conv (str):
    def sub_syms (m):
	syms =  m.group (1).split ()
	tags = ["\\tag #'%s" % s for s in syms]
	return ' '.join (tags)

    str = re.sub (r"\\tag #'\(([^)]+)\)",  sub_syms, str)
    return str


@rule ((2, 7, 24), _ ('deprecate %s') % 'number-visibility')
def conv (str):
    str = re.sub (r"#'number-visibility",
		  "#'number-visibility % number-visibility is deprecated. Tune the TupletNumber instead\n",
		  str)
    return str


@rule ((2, 7, 28), "ly:spanner-get-bound -> ly:spanner-bound")
def conv (str):
    str = re.sub (r"ly:spanner-get-bound", "ly:spanner-bound", str)
    return str


@rule ((2, 7, 29), "override Stem #'beamed-* -> #'details #'beamed-*")
def conv (str):
    for a in ['beamed-lengths', 'beamed-minimum-free-lengths',
              'lengths',
	      'beamed-extreme-minimum-free-lengths']:
	str = re.sub (r"\\override\s+Stem\s+#'%s" % a,
		      r"\\override Stem #'details #'%s" % a,
		      str)
    return str


@rule ((2, 7, 30), "\\epsfile")
def conv (str):
    str = re.sub (r'\\epsfile *#"', r'\\epsfile #X #10 #"', str)
    return str


@rule ((2, 7, 31), "Foo_bar::bla_bla -> ly:foo-bar::bla-bla")
def conv (str):
    def sub_cxx_id (m):
	str = m.group(1)
	return 'ly:' + str.lower ().replace ('_','-')

    str = re.sub (r'([A-Z][a-z_0-9]+::[a-z_0-9]+)',
		  sub_cxx_id, str)
    return str


@rule ((2, 7, 32), _ ("foobar -> foo-bar for \paper, \layout"))
def conv (str):
    identifier_subs = [
	    ('inputencoding', 'input-encoding'),
	    ('printpagenumber', 'print-page-number'),
	    ('outputscale', 'output-scale'),
	    ('betweensystemspace', 'between-system-space'),
	    ('betweensystempadding', 'between-system-padding'),
	    ('pagetopspace', 'page-top-space'),
	    ('raggedlastbottom', 'ragged-last-bottom'),
	    ('raggedright', 'ragged-right'),
	    ('raggedlast', 'ragged-last'),
	    ('raggedbottom', 'ragged-bottom'),
	    ('aftertitlespace', 'after-title-space'),
	    ('beforetitlespace', 'before-title-space'),
	    ('betweentitlespace', 'between-title-space'),
	    ('topmargin', 'top-margin'),
	    ('bottommargin', 'bottom-margin'),
	    ('headsep', 'head-separation'),
	    ('footsep', 'foot-separation'),
	    ('rightmargin', 'right-margin'),
	    ('leftmargin', 'left-margin'),
	    ('printfirstpagenumber', 'print-first-page-number'),
	    ('firstpagenumber', 'first-page-number'),
	    ('hsize', 'paper-width'),
	    ('vsize', 'paper-height'),
	    ('horizontalshift', 'horizontal-shift'),
	    ('staffspace', 'staff-space'),
	    ('linethickness', 'line-thickness'),
	    ('ledgerlinethickness', 'ledger-line-thickness'),
	    ('blotdiameter', 'blot-diameter'),
	    ('staffheight', 'staff-height'),
	    ('linewidth', 'line-width'),
	    ('annotatespacing', 'annotate-spacing')
	    ]

    for (a,b)  in identifier_subs:
	### for C++:
	## str = re.sub ('"%s"' % a, '"%s"' b, str)

	str = re.sub (a, b, str)
    return str


@rule ((2, 7, 32), "debug-beam-quanting -> debug-beam-scoring")
def conv (str):
    str = re.sub ('debug-beam-quanting', 'debug-beam-scoring', str)
    return str


@rule ((2, 7, 36), "def-(music-function|markup-command) -> define-(music-function|markup-command)")
def conv (str):
    str = re.sub ('def-music-function', 'define-music-function', str)
    str = re.sub ('def-markup-command', 'define-markup-command', str)
    return str


@rule ((2, 7, 40), "rehearsalMarkAlignSymbol/barNumberAlignSymbol -> break-align-symbol")
def conv (str):
    str = re.sub (r'\\set\s+Score\s*\.\s*barNumberAlignSymbol\s*=',
		  r"\\override Score.BarNumber #'break-align-symbol = ", str)
    str = re.sub (r'\\set\s*Score\s*\.\s*rehearsalMarkAlignSymbol\s*=',
		  r"\\override Score.RehearsalMark #'break-align-symbol = ", str)
    return str


@rule ((2, 9, 4), "(page-)penalty -> (page-)break-penalty")
def conv (str):
    str = re.sub ('page-penalty', 'page-break-penalty', str)
    str = re.sub ('([^-])penalty', '\1break-penalty', str)
    return str


@rule ((2, 9, 6), "\\context Foo \\applyOutput #bla -> \\applyOutput #'Foo #bla ")
def conv (str):
    str = re.sub (r'\\context\s+\"?([a-zA-Z]+)\"?\s*\\applyOutput', r"\\applyOutput #'\1", str)
    return str


@rule ((2, 9, 9), "annotatefoo -> annotate-foo")
def conv (str):
    str = re.sub ('annotatepage', 'annotate-page', str)
    str = re.sub ('annotateheaders', 'annotate-headers', str)
    str = re.sub ('annotatesystems', 'annotate-systems', str)
    return str


@rule ((2, 9, 11), "\\set tupletNumberFormatFunction -> \\override #'text = ")
def conv (str):
    str = re.sub (r"""(\\set\s)?(?P<context>[a-zA-Z]*.?)tupletNumberFormatFunction\s*=\s*#denominator-tuplet-formatter""",
                  r"""\\override \g<context>TupletNumber #'text = #tuplet-number::calc-denominator-text""", str)

    str = re.sub (r"""(\\set\s+)?(?P<context>[a-zA-Z]*.?)tupletNumberFormatFunction\s*=\s*#fraction-tuplet-formatter""",
                  r"""\\override \g<context>TupletNumber #'text = #tuplet-number::calc-fraction-text""", str)

    if re.search ('tupletNumberFormatFunction', str):
        stderr_write ("\n")
	stderr_write ("tupletNumberFormatFunction has been removed. Use #'text property on TupletNumber")
        stderr_write ("\n")
    return str


@rule ((2, 9, 13), "instrument -> instrumentName, instr -> shortInstrumentName, vocNam -> shortVocalName")
def conv (str):
    str = re.sub ('vocNam', 'shortVocalName', str)
    str = re.sub (r'\.instr\s*=', r'.shortInstrumentName =', str)
    str = re.sub (r'\.instrument\s*=', r'.instrumentName =', str)
    return str


@rule ((2, 9, 16), _ ("deprecate \\tempo in \\midi"))
def conv (str):

    def sub_tempo (m):
        dur = int (m.group (1))
        dots = len (m.group (2))
        count = int (m.group (3))

        log2 = 0
        while dur > 1 :
            dur /= 2
            log2 += 1
        
        den = (1 << dots) * (1 << log2)
        num = ((1 << (dots+1))  - 1)

        return  """
  \midi {
    \context {
      \Score
      tempoWholesPerMinute = #(ly:make-moment %d %d)
      }
    }

""" % (num*count, den)
    
    str = re.sub (r'\\midi\s*{\s*\\tempo ([0-9]+)\s*([.]*)\s*=\s*([0-9]+)\s*}', sub_tempo, str)
    return str


@rule ((2, 9, 19), "printfirst-page-number -> print-first-page-number")
def conv (str):
    str = re.sub ('printfirst-page-number', 'print-first-page-number', str)
    return str


@rule ((2, 10, 0), _ ("bump version for release"))
def conv (str):
    return str


@rule ((2, 11, 2), "ly:clone-parser -> ly:parser-clone")
def conv (str):
    return re.sub ('ly:clone-parser',
                   'ly:parser-clone', str)


@rule ((2, 11, 5), _ ("deprecate cautionary-style. Use AccidentalCautionary properties"))
def conv (str):
    str = re.sub ("Accidental\s*#'cautionary-style\s*=\s*#'smaller",
                   "AccidentalCautionary #'font-size = #-2", str)
    str = re.sub ("Accidental\s*#'cautionary-style\s*=\s*#'parentheses",
                   "AccidentalCautionary #'parenthesized = ##t", str)
    str = re.sub ("([A-Za-z]+)\s*#'cautionary-style\s*=\s*#'parentheses",
                   r"\1 #'parenthesized = ##t", str)
    str = re.sub ("([A-Za-z]+)\s*#'cautionary-style\s*=\s*#'smaller",
                   r"\1 #'font-size = #-2", str)
    return str


@rule ((2, 11, 6), _ ("Rename accidental glyphs, use glyph-name-alist."))
def conv (str):
    
    def sub_acc_name (m):
        idx = int (m.group (1).replace ('M','-'))
        
        return ["accidentals.doublesharp",
                "accidentals.sharp.slashslash.stemstemstem",
                "accidentals.sharp",
                "accidentals.sharp.slashslash.stem",
                "accidentals.natural",
                "accidentals.mirroredflat",
                "accidentals.flat",
                "accidentals.mirroredflat.flat",
                "accidentals.flatflat"][4-idx]

    str = re.sub (r"accidentals[.](M?[-0-9]+)",
                  sub_acc_name, str) 
    str = re.sub (r"(KeySignature|Accidental[A-Za-z]*)\s*#'style\s*=\s*#'([a-z]+)",
                  r"\1 #'glyph-name-alist = #alteration-\2-glyph-name-alist", str)
    ## FIXME: standard vs default, alteration-FOO vs FOO-alteration
    str = str.replace ('alteration-default-glyph-name-alist',
                       'standard-alteration-glyph-name-alist')
    return str


@rule ((2, 11, 10), """allowBeamBreak -> Beam #'breakable = ##t
addquote -> addQuote
""")
def conv (str):
    str = re.sub (r'(\\set\s+)?([A-Z][a-zA-Z]+\s*\.\s*)allowBeamBreak',
                  r"\override \2Beam #'breakable", str)
    str = re.sub (r'(\\set\s+)?allowBeamBreak',
                  r"\override Beam #'breakable", str)
    str = re.sub (r'addquote', 'addQuote', str)
    if re.search ("Span_dynamic_performer", str):
        stderr_write ("Span_dynamic_performer has been merged into Dynamic_performer")

    return str


@rule ((2, 11, 11), "layout-set-staff-size -> layout-set-absolute-staff-size")
def conv (str):
    str = re.sub (r'\(layout-set-staff-size \(\*\s*([0-9.]+)\s*(pt|mm|cm)\)\)',
                  r'(layout-set-absolute-staff-size (* \1 \2))', str)
    return str


@rule ((2, 11, 13), "#'arrow = ##t -> #'bound-details #'right #'arrow = ##t")
def conv (str):
    str = re.sub (r"\\override\s*([a-zA-Z.]+)\s*#'arrow\s*=\s*##t",
                  r"\\override \1 #'bound-details #'right #'arrow = ##t",
                  str)

    if re.search ('edge-text', str):
	stderr_write (NOT_SMART % _ ("edge-text settings for TextSpanner."))
	stderr_write (_ ("Use\n\n%s") %
                          "\t\\override TextSpanner #'bound-details #'right #'text = <right-text>\n"
                          "\t\\override TextSpanner #'bound-details #'left #'text = <left-text>\n")
    return str


@rule ((2, 11, 15), "TextSpanner #'edge-height -> #'bound-details #'right/left #'text = ...")
def conv (str):
    def sub_edge_height (m):
        s = ''
        for (var, h) in [('left', m.group (3)),
                         ('right', m.group (4))]:

            if h and float (h):
                once = m.group (1)
                if not once:
                    once = ''
                context = m.group (2)
                if not context:
                    context = ''
                    
                s += (r"%s \override %sTextSpanner #'bound-details #'%s #'text = \markup { \draw-line #'(0 . %s) }"
                      % (once, context, var, h))

                s += '\n'
            
        return s
    
                  
    str = re.sub (r"(\\once)?\s*\\override\s*([a-zA-Z]+\s*[.]\s*)?TextSpanner\s*#'edge-height\s*=\s*#'\(\s*([0-9.-]+)\s+[.]\s+([0-9.-]+)\s*\)", sub_edge_height, str)
    return str


@rule ((2, 11, 23), "#'break-align-symbol -> #'break-align-symbols")
def conv (str):
    str = re.sub (r"\\override\s*([a-zA-Z.]+)\s*#'break-align-symbol\s*=\s*#'([a-z-]+)",
                  r"\\override \1 #'break-align-symbols = #'(\2)", str)
    return str


@rule ((2, 11, 35), """scripts.caesura -> scripts.caesura.curved.
""" + _ ("Use #'style not #'dash-fraction to select solid/dashed lines."))
def conv (str):
    str = re.sub (r"scripts\.caesura",
                  r"scripts.caesura.curved", str)

    if re.search ('dash-fraction', str):
	stderr_write (NOT_SMART % _ ("all settings related to dashed lines.\n"))
	stderr_write (_ ("Use \\override ... #'style = #'line for solid lines and\n"))
	stderr_write (_ ("\t\\override ... #'style = #'dashed-line for dashed lines."))
    return str


@rule ((2, 11, 38), """\\setEasyHeads -> \\easyHeadsOn, \\fatText -> \\textLengthOn,
\\emptyText -> \\textLengthOff""")
def conv (str):
    str = re.sub (r"setEasyHeads", r"easyHeadsOn", str)
    str = re.sub (r"fatText", r"textLengthOn", str)
    str = re.sub (r"emptyText", r"textLengthOff", str)
    return str


@rule ((2, 11, 46), "\\set hairpinToBarline -> \\override Hairpin #'to-barline")
def conv (str):
    str = re.sub (r"\\set\s+([a-zA-Z]+)\s*.\s*hairpinToBarline\s*=\s*##([tf]+)",
                  r"\\override \1.Hairpin #'to-barline = ##\2", str)
    str = re.sub (r"\\set\s+hairpinToBarline\s*=\s*##([tf]+)",
                  r"\\override Hairpin #'to-barline = ##\1", str)
    str = re.sub (r"\\unset\s+([a-zA-Z]+)\s*.\s*hairpinToBarline",
                  r"\\revert \1.Hairpin #'to-barline", str)
    str = re.sub (r"\\unset\s+hairpinToBarline",
                  r"\\revert Hairpin #'to-barline", str)
    str = re.sub (r"hairpinToBarline\s*=\s*##([tf]+)",
                  r"\\override Hairpin #'to-barline = ##\1", str)
    str = re.sub (r"\\set (de|)crescendoSpanner = #'dashed-line",
                  r"\\set \1crescendoSpanner = #'text", str)
    return str


@rule ((2, 11, 48), "\\compressMusic -> \\scaleDurations")
def conv (str):
    str = re.sub (r"compressMusic", r"scaleDurations", str)
    return str


@rule ((2, 11, 50), _ ("metronomeMarkFormatter uses text markup as second argument,\n\
fret diagram properties moved to fret-diagram-details."))
def conv (str):
    ## warning 1/2: metronomeMarkFormatter uses text markup as second argument
    if re.search ('metronomeMarkFormatter', str):
	stderr_write (NOT_SMART % _ ("metronomeMarkFormatter got an additional text argument.\n"))
	stderr_write (_ ("The function assigned to Score.metronomeMarkFunction now uses the signature\n%s") %
                          "\t(format-metronome-markup text dur count context)\n")

    ## warning 2/2: fret diagram properties moved to fret-diagram-details
    fret_props = ['barre-type', 
                'dot-color', 
                'dot-radius',
                'finger-code',
                'fret-count',
                'label-dir',
                'number-type',
                'string-count',
                'xo-font-magnification',
                'mute-string',
                'open-string',
                'orientation']
    for prop in fret_props:
      if re.search (prop, str):
          stderr_write (NOT_SMART %
            prop + " in fret-diagram properties. Use fret-diagram-details.")
          stderr_write ('\n')
    return str

@rule ((2, 11, 51), "\\octave -> \\octaveCheck, \\arpeggioUp -> \\arpeggioArrowUp,\n\
\\arpeggioDown -> \\arpeggioArrowDown, \\arpeggioNeutral -> \\arpeggioNormal,\n\
\\setTextCresc -> \\crescTextCresc, \\setTextDecresc -> \\dimTextDecresc,\n\
\\setTextDecr -> \\dimTextDecr, \\setTextDim -> \\dimTextDim,\n\
\\setHairpinCresc -> \\crescHairpin, \\setHairpinDecresc -> \\dimHairpin,\n\
\\sustainUp -> \\sustainOff, \\sustainDown -> \\sustainOn\n\
\\sostenutoDown -> \\sostenutoOn, \\sostenutoUp -> \\sostenutoOff")
def conv (str):
    str = re.sub (r"\\octave", r"\\octaveCheck", str)
    str = re.sub (r"arpeggioUp", r"arpeggioArrowUp", str)
    str = re.sub (r"arpeggioDown", r"arpeggioArrowDown", str)
    str = re.sub (r"arpeggioNeutral", r"arpeggioNormal", str)
    str = re.sub (r"setTextCresc", r"crescTextCresc", str)
    str = re.sub (r"setTextDecresc", r"dimTextDecresc", str)
    str = re.sub (r"setTextDecr", r"dimTextDecr", str)
    str = re.sub (r"setTextDim", r"dimTextDim", str)
    str = re.sub (r"setHairpinCresc", r"crescHairpin", str)
    str = re.sub (r"setHairpinDecresc", r"dimHairpin", str)
    str = re.sub (r"sustainUp", r"sustainOff", str)
    str = re.sub (r"sustainDown", r"sustainOn", str)
    str = re.sub (r"sostenutoDown", r"sostenutoOn", str)
    str = re.sub (r"sostenutoUp", r"sostenutoOff", str)
    return str

@rule ((2, 11, 52), "\\setHairpinDim -> \\dimHairpin")
def conv (str):
    str = str.replace ("setHairpinDim", "dimHairpin")
    return str

@rule ((2, 11, 53), "infinite-spacing-height -> extra-spacing-height")
def conv (str):
    str = re.sub (r"infinite-spacing-height\s+=\s+##t", r"extra-spacing-height = #'(-inf.0 . +inf.0)", str)
    str = re.sub (r"infinite-spacing-height\s+=\s+##f", r"extra-spacing-height = #'(0 . 0)", str)
    return str

@rule ((2, 11, 55), "#(set-octavation oct) -> \\ottava #oct,\n\
\\put-adjacent markup axis dir markup -> \\put-adjacent axis dir markup markup")
def conv (str):    
    str = re.sub (r"#\(set-octavation (-*[0-9]+)\)", r"\\ottava #\1", str)
    if re.search ('put-adjacent', str):
	stderr_write (NOT_SMART % _ ("\\put-adjacent argument order.\n"))
	stderr_write (_ ("Axis and direction now come before markups:\n"))
	stderr_write (_ ("\\put-adjacent axis dir markup markup."))
    return str

@rule ((2, 11, 57), "\\center-align -> \\center-column, \\hcenter -> \\center-align")
def conv (str):
    str = re.sub (r"([\\:]+)center-align", r"\1center-column", str)
    str = re.sub (r"hcenter(\s+)", r"center-align\1", str)
    return str

@rule ((2, 11, 60), "printallheaders -> print-all-headers")
def conv (str):
    str = re.sub (r"printallheaders", r"print-all-headers", str)
    return str

@rule ((2, 11, 61), "gregorian-init.ly -> gregorian.ly")
def conv (str):
    str = re.sub (r'\\include(\s+)"gregorian-init.ly"', r'\\include\1"gregorian.ly"', str)
    return str

@rule ((2, 11, 62), "makam-init.ly -> makam.ly, \\bigger -> \\larger")
def conv (str):
    str = re.sub (r'\\include(\s+)"makam-init.ly"', r'\\include\1"makam.ly"', str)
    str = re.sub (r"([\\:])bigger", r"\1larger", str)
    return str

@rule ((2, 11, 64), "systemSeparatorMarkup -> system-separator-markup,\n\
InnerStaffGroup -> StaffGroup, InnerChoirStaff -> ChoirStaff")
def conv (str):
    str = re.sub (r'systemSeparatorMarkup', r'system-separator-markup', str)
    if re.search (r'\\InnerStaffGroup', str):
        stderr_write ("\n")
        stderr_write (NOT_SMART % _("re-definition of InnerStaffGroup.\n"))
        stderr_write (FROM_TO % ("InnerStaffGroup", "StaffGroup.\n"))
        stderr_write (UPDATE_MANUALLY)
        raise FatalConversionError ()
    if re.search (r'\\InnerChoirStaff', str):
        stderr_write ("\n")
        stderr_write (NOT_SMART % _("re-definition of InnerChoirStaff.\n"))
        stderr_write (FROM_TO % ("InnerChoirStaff", "ChoirStaff.\n"))
        stderr_write (UPDATE_MANUALLY)
        raise FatalConversionError ()
    else:
        str = re.sub ('InnerStaffGroup', 'StaffGroup', str)
        str = re.sub ('InnerChoirStaff', 'ChoirStaff', str)
    return str

@rule ((2, 12, 0),
       _ ("Syntax changes for \\addChordShape and \\chord-shape") + "\n" + \
       _ ("bump version for release"))
def conv(str):
    if re.search(r'\\addChordShape', str):
        stderr_write ("\n")
        stderr_write (NOT_SMART % _("stringTuning must be added to \
addChordShape call.\n"))
        stderr_write (UPDATE_MANUALLY)
        raise FatalConversionError ()
    if re.search (r'\\chord-shape', str):
        stderr_write ("\n")
        stderr_write (NOT_SMART % _("stringTuning must be added to \
chord-shape call.\n"))
        stderr_write (UPDATE_MANUALLY)
        raise FatalConversionError ()
    return str

# Guidelines to write rules (please keep this at the end of this file)
#
# - keep at most one rule per version; if several conversions should be done,
# concatenate them into a single "conv" function;
#
# - enclose strings to be localized with `_(' and  `)';
#
# - write rule for bumping major stable version with
#
#     _ ("bump version for release")
#  
# as exact description.
