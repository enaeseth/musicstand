% common german names for notes. "es" means flat, "is" means sharp
%
% by Roland Meier <<meier@informatik.th-darmstadt.de>>
% based on swedish.ly by Mats Bengtsson.

% 1999/06/09 Bjoern Jacke <<bjoern.jacke@gmx.de>>
%            added asas and marked ases as `unusual'


pitchnamesDeutsch = #`(
	(ceses . ,(ly:make-pitch -1 0 DOUBLE-FLAT))
	(ceseh . ,(ly:make-pitch -1 0 THREE-Q-FLAT))
	(ces . ,(ly:make-pitch -1 0 FLAT))
	(ceh . ,(ly:make-pitch -1 0 SEMI-FLAT))
	(c . ,(ly:make-pitch -1 0 NATURAL))
	(cih . ,(ly:make-pitch -1 0 SEMI-SHARP))
	(cis . ,(ly:make-pitch -1 0 SHARP))
	(cisih . ,(ly:make-pitch -1 0 THREE-Q-SHARP))
	(cisis . ,(ly:make-pitch -1 0 DOUBLE-SHARP))

	(deses . ,(ly:make-pitch -1 1 DOUBLE-FLAT))
	(deseh . ,(ly:make-pitch -1 1 THREE-Q-FLAT))
	(des . ,(ly:make-pitch -1 1 FLAT))
	(deh . ,(ly:make-pitch -1 1 SEMI-FLAT))
	(d . ,(ly:make-pitch -1 1 NATURAL))
	(dih . ,(ly:make-pitch -1 1 SEMI-SHARP))
	(dis . ,(ly:make-pitch -1 1 SHARP))
	(disih . ,(ly:make-pitch -1 1 THREE-Q-SHARP))
	(disis . ,(ly:make-pitch -1 1 DOUBLE-SHARP))

	(eses . ,(ly:make-pitch -1 2 DOUBLE-FLAT))
	(eseh . ,(ly:make-pitch -1 2 THREE-Q-FLAT))
	(es . ,(ly:make-pitch -1 2 FLAT))
	(eeh . ,(ly:make-pitch -1 2 SEMI-FLAT))
	(e . ,(ly:make-pitch -1 2 NATURAL))
	(eih . ,(ly:make-pitch -1 2 SEMI-SHARP))
	(eis . ,(ly:make-pitch -1 2 SHARP))
	(eisih . ,(ly:make-pitch -1 2 THREE-Q-SHARP))
	(eisis . ,(ly:make-pitch -1 2 DOUBLE-SHARP))

	(feses . ,(ly:make-pitch -1 3 DOUBLE-FLAT))
	(feseh . ,(ly:make-pitch -1 3 THREE-Q-FLAT))
	(fes . ,(ly:make-pitch -1 3 FLAT))
	(feh . ,(ly:make-pitch -1 3 SEMI-FLAT))
	(f . ,(ly:make-pitch -1 3 NATURAL))
	(fih . ,(ly:make-pitch -1 3 SEMI-SHARP))
	(fis . ,(ly:make-pitch -1 3 SHARP))
	(fisih . ,(ly:make-pitch -1 3 THREE-Q-SHARP))
	(fisis . ,(ly:make-pitch -1 3 DOUBLE-SHARP))

	(geses . ,(ly:make-pitch -1 4 DOUBLE-FLAT))
	(geseh . ,(ly:make-pitch -1 4 THREE-Q-FLAT))
	(ges . ,(ly:make-pitch -1 4 FLAT))
	(geh . ,(ly:make-pitch -1 4 SEMI-FLAT))
	(g . ,(ly:make-pitch -1 4 NATURAL))
	(gih . ,(ly:make-pitch -1 4 SEMI-SHARP))
	(gis . ,(ly:make-pitch -1 4 SHARP))
	(gisih . ,(ly:make-pitch -1 4 THREE-Q-SHARP))
	(gisis . ,(ly:make-pitch -1 4 DOUBLE-SHARP))

	(asas . ,(ly:make-pitch -1 5 DOUBLE-FLAT))
	(asah . ,(ly:make-pitch -1 5 THREE-Q-FLAT))
	(ases . ,(ly:make-pitch -1 5 DOUBLE-FLAT))   ;;non-standard name for asas
	(aseh . ,(ly:make-pitch -1 5 THREE-Q-FLAT))
	(as . ,(ly:make-pitch -1 5 FLAT))
	(aeh . ,(ly:make-pitch -1 5 SEMI-FLAT))
	(a . ,(ly:make-pitch -1 5 NATURAL))
	(aih . ,(ly:make-pitch -1 5 SEMI-SHARP))
	(ais . ,(ly:make-pitch -1 5 SHARP))
	(aisih . ,(ly:make-pitch -1 5 THREE-Q-SHARP))
	(aisis . ,(ly:make-pitch -1 5 DOUBLE-SHARP))

	(heses . ,(ly:make-pitch -1 6 DOUBLE-FLAT))
	(heseh . ,(ly:make-pitch -1 6 THREE-Q-FLAT))
	(b . ,(ly:make-pitch -1 6 FLAT))
	(beh . ,(ly:make-pitch -1 6 SEMI-FLAT))
	(h . ,(ly:make-pitch -1 6 NATURAL))
	(hih . ,(ly:make-pitch -1 6 SEMI-SHARP))
	(his . ,(ly:make-pitch -1 6 SHARP))
	(hisih . ,(ly:make-pitch -1 6 THREE-Q-SHARP))
	(hisis . ,(ly:make-pitch -1 6 DOUBLE-SHARP))
)


pitchnames = \pitchnamesDeutsch

\version "2.12.0"

#(ly:parser-set-note-names parser pitchnames)
