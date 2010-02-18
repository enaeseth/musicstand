\score {

\relative c''
{

    e4 b8 c d4 c8 b a4 a8 c e4 d8 c b4. c8 d4 e c a a2
    r8 d4 f8 a4 g8 f e4. c8 e4 d8 c b4 b8 c d4 e c a a2
    e'4 b8 c d4 c8 b a4 a8 c e4 d8 c b4. c8 d4 e c a a2
    r8 d4 f8 a4 g8 f e4. c8 e4 d8 c b4 b8 c d4 e c a a2
    e'2 c d b c a 
    gis1 e'2 c d b c4 e a2 gis1


}


\midi {
    \context {
      \Score
      tempoWholesPerMinute = #(ly:make-moment 160 4)
    }
 }
\layout { }
}
\version "2.12.2"
