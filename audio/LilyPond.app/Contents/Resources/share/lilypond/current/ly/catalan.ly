%{

 Common catalan names for notes. "b" means flat (bemoll), "d" means sharp
 (diesi).  Also "s" is included for sharp (sostingut).  Both "diesi" and
 "sostingut" are approved by "Diccionari de la Llengua Catalana" from
 "Institut d'Estudis Catalans".

 Adapted from italiano.ly.

 English: a   b   c   d   e   f   g
 Catalan: la  si  do  re  mi  fa  sol

 For spanish naming just use the sharp sign "s" (sostenido) instead of "s"
(sostenido) .
%}

% contributed by Jaume Obrador <<jobrador@ipc4.uib.es>>


% For using "sostingut" notation, which is also correct
pitchnamesCatalan = #`(
	(dobb . ,(ly:make-pitch -1 0 DOUBLE-FLAT))
	(dob . ,(ly:make-pitch -1 0 FLAT))
	(do . ,(ly:make-pitch -1 0 NATURAL))
	(dod . ,(ly:make-pitch -1 0 SHARP))
	(dodd . ,(ly:make-pitch -1 0 DOUBLE-SHARP))
	(rebb . ,(ly:make-pitch -1 1 DOUBLE-FLAT))
	(reb . ,(ly:make-pitch -1 1 FLAT))
	(re . ,(ly:make-pitch -1 1 NATURAL))
	(red . ,(ly:make-pitch -1 1 SHARP))
	(redd . ,(ly:make-pitch -1 1 DOUBLE-SHARP))
	(mibb . ,(ly:make-pitch -1 2 DOUBLE-FLAT))
	(mib . ,(ly:make-pitch -1 2 FLAT))
	(mi . ,(ly:make-pitch -1 2 NATURAL))
	(mid . ,(ly:make-pitch -1 2 SHARP))
	(midd . ,(ly:make-pitch -1 2 DOUBLE-SHARP))
	(fabb . ,(ly:make-pitch -1 3 DOUBLE-FLAT))
	(fab . ,(ly:make-pitch -1 3 FLAT))
	(fa . ,(ly:make-pitch -1 3 NATURAL))
	(fad . ,(ly:make-pitch -1 3 SHARP))
	(fadd . ,(ly:make-pitch -1 3 DOUBLE-SHARP))
	(solbb . ,(ly:make-pitch -1 4 DOUBLE-FLAT))
	(solb . ,(ly:make-pitch -1 4 FLAT))
	(sol . ,(ly:make-pitch -1 4 NATURAL))
	(sold . ,(ly:make-pitch -1 4 SHARP))
	(soldd . ,(ly:make-pitch -1 4 DOUBLE-SHARP))
	(labb . ,(ly:make-pitch -1 5 DOUBLE-FLAT))
	(lab . ,(ly:make-pitch -1 5 FLAT))
	(la . ,(ly:make-pitch -1 5 NATURAL))
	(lad . ,(ly:make-pitch -1 5 SHARP))
	(ladd . ,(ly:make-pitch -1 5 DOUBLE-SHARP))
	(sibb . ,(ly:make-pitch -1 6 DOUBLE-FLAT))
	(sib . ,(ly:make-pitch -1 6 FLAT))
	(si . ,(ly:make-pitch -1 6 NATURAL))
	(sid . ,(ly:make-pitch -1 6 SHARP))
	(sidd . ,(ly:make-pitch -1 6 DOUBLE-SHARP))

	;; Now that we have espanol.ly, should these be junked? --jcn
	(dos . ,(ly:make-pitch -1 0 SHARP))
	(doss . ,(ly:make-pitch -1 0 DOUBLE-SHARP))
	(res . ,(ly:make-pitch -1 1 SHARP))
	(ress . ,(ly:make-pitch -1 1 DOUBLE-SHARP))
	(mis . ,(ly:make-pitch -1 2 SHARP))
	(miss . ,(ly:make-pitch -1 2 DOUBLE-SHARP))
	(fas . ,(ly:make-pitch -1 3 SHARP))
	(fass . ,(ly:make-pitch -1 3 DOUBLE-SHARP))
	(sols . ,(ly:make-pitch -1 4 SHARP))
	(solss . ,(ly:make-pitch -1 4 DOUBLE-SHARP))
	(las . ,(ly:make-pitch -1 5 SHARP))
	(lass . ,(ly:make-pitch -1 5 DOUBLE-SHARP))
	(sis . ,(ly:make-pitch -1 6 SHARP))
	(siss . ,(ly:make-pitch -1 6 DOUBLE-SHARP))
)

pitchnames = \pitchnamesCatalan

\version "2.12.0"

#(ly:parser-set-note-names parser pitchnames)
