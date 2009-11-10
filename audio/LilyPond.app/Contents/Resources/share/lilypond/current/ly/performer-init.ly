\version "2.12.0"

%%
%% setup for Request->Element conversion. 
%%
\context {
    \type "Performer_group"
    \name Staff
    \accepts Voice
    \accepts CueVoice
    \defaultchild Voice
    
    \consists "Staff_performer"
    \consists "Key_performer"
}
\context {
    \name Global
    \accepts Score
\description "Hard coded entry point for LilyPond. Cannot be tuned."
    }

\context {
    \Staff
    \name DrumStaff
    midiInstrument = #"drums"
    \accepts DrumVoice
    \defaultchild DrumVoice
}

\context {
    \type "Performer_group"
    \name Voice
    \consists "Dynamic_performer"    
    \consists "Tie_performer"
    \consists "Piano_pedal_performer"
    \consists "Note_performer"
    \consists "Beam_performer"
    \consists "Slur_performer"
}

\context {
  \Voice
  \name CueVoice
  \alias Voice
}

\context {
  \Voice
  \name VaticanaVoice
  \alias Voice
}

\context {
    \Voice
    \remove "Note_performer"
    \consists "Drum_note_performer" 
    \name DrumVoice
}

\context {
    \type "Performer_group"
    \name FiguredBass 
    \consists "Swallow_performer"
}

\context {
    \type "Performer_group"
    \name GrandStaff
    \accepts RhythmicStaff
    \accepts Staff
    \defaultchild Staff
}

\context {
    \type "Performer_group"
    \name "PianoStaff"
    \accepts Staff
    \accepts DrumStaff
    \defaultchild Staff
}

\context {
    \type "Performer_group"
    \name "TabVoice"
    \consists "Swallow_performer"
}

\context {
    \type "Performer_group"
    \name "Devnull"
    \consists "Swallow_performer"
}
\context {
    \type "Performer_group"
    \name "TabStaff"
    \accepts "TabVoice"
    \defaultchild "TabVoice"
}

\context {
    \type "Performer_group"
    \name "VaticanaStaff"
    \alias "Staff"
    \denies "Voice"
    \accepts "VaticanaVoice"
    \defaultchild "VaticanaVoice"
}

\context {
    \type "Score_performer"

    \name Score
    
    melismaBusyProperties = #default-melisma-properties
    instrumentName = #"bright acoustic"

    %% quarter = 60
    tempoWholesPerMinute = #(ly:make-moment 15 1)
    
    \accepts Staff
    \accepts DrumStaff
    \accepts GrandStaff
    \accepts PianoStaff
    \accepts TabStaff
    \accepts Staff
    \accepts StaffGroup
    \accepts Devnull
    \accepts ChoirStaff
    \accepts RhythmicStaff
    \accepts ChordNames
    \accepts FiguredBass
    \accepts Lyrics
    \accepts VaticanaStaff

    \consists "Time_signature_performer"
    \consists "Control_track_performer"
    \consists "Tempo_performer"
    \consists "Timing_translator"
    \consists "Swallow_performer"
    
    \defaultchild "Staff"
    
    dynamicAbsoluteVolumeFunction = #default-dynamic-absolute-volume
    instrumentEqualizer = #default-instrument-equalizer
    drumPitchTable = #(alist->hash-table midiDrumPitches)
    timing = ##t 
}


\context {
    \type "Performer_group"
    \consists "Staff_performer" % Performer_group ?
    \consists "Lyric_performer"
    \name Lyrics
}

\context{
    \type "Performer_group"
    \name ChoirStaff
    \accepts Staff
    \accepts DrumStaff
    \defaultchild Staff

}



\context {
    \type "Performer_group"
    \consists "Staff_performer"
    \accepts ChordNameVoice
    \name ChordNames
}

\context {
    \type "Performer_group"
    \consists "Note_performer"
    \name ChordNameVoice	
}

\context {
    \type "Performer_group"

    \name StaffGroup
    \accepts Staff
    \accepts DrumStaff
    \accepts TabStaff
    \accepts RhythmicStaff
    \accepts GrandStaff
    \accepts PianoStaff
    \accepts Lyrics
    \accepts ChordNames
    \accepts FiguredBass

    \defaultchild Staff
}

\context { \Staff \name RhythmicStaff }


