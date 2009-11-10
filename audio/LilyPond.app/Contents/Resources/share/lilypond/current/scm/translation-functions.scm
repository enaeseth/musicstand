;;;; translation-functions.scm --
;;;;
;;;;  source file of the GNU LilyPond music typesetter
;;;; 
;;;; (c) 1998--2009 Han-Wen Nienhuys <hanwen@xs4all.nl>
;;;;		     Jan Nieuwenhuizen <janneke@gnu.org>

;; metronome marks
(define-public (format-metronome-markup text dur count context)
  (let* ((hide-note (eq? #t (ly:context-property context 'tempoHideNote))))
    (metronome-markup text dur count hide-note)))

(define-public (metronome-markup text dur count hide-note)
  (let* ((note-mark (if (and (not hide-note) (ly:duration? dur))
                      (make-smaller-markup
		       (make-note-by-number-markup (ly:duration-log dur)
						   (ly:duration-dot-count dur)
						   1))
		      #f))
         (note-markup (if (and (not hide-note) (number? count) (> count 0) )
                        (make-concat-markup (list
                          (make-general-align-markup Y DOWN note-mark)
                          (make-simple-markup " ")
                          (make-simple-markup "=")
                          (make-simple-markup " ")
                          (make-simple-markup (number->string count))))
                      #f))
         (text-markup (if (not (null? text))
                        (make-bold-markup text)
                        #f)))
    (if text-markup
      (if (and note-markup (not hide-note))
        (make-line-markup (list text-markup
          (make-concat-markup (list (make-simple-markup "(")
                                    note-markup
                                    (make-simple-markup ")")))))
        (make-line-markup (list text-markup)))
      (if note-markup
        (make-line-markup (list note-markup))
        (make-null-markup)))))

(define-public (format-mark-alphabet mark context)
  (make-bold-markup (make-markalphabet-markup (1- mark))))

(define-public (format-mark-box-alphabet mark context)
  (make-bold-markup (make-box-markup (make-markalphabet-markup (1- mark)))))

(define-public (format-mark-circle-alphabet mark context)
  (make-bold-markup (make-circle-markup (make-markalphabet-markup (1- mark)))))

(define-public (format-mark-letters mark context)
  (make-bold-markup (make-markletter-markup (1- mark))))

(define-public (format-mark-numbers mark context)
  (make-bold-markup (number->string mark)))

(define-public (format-mark-barnumbers mark context)
  (make-bold-markup (number->string (ly:context-property context 'currentBarNumber))))

(define-public (format-mark-box-letters mark context)
  (make-bold-markup (make-box-markup (make-markletter-markup (1- mark)))))

(define-public (format-mark-circle-letters mark context)
  (make-bold-markup (make-circle-markup (make-markletter-markup (1- mark)))))

(define-public (format-mark-box-numbers mark context)
  (make-bold-markup (make-box-markup (number->string mark))))

(define-public (format-mark-circle-numbers mark context)
  (make-bold-markup (make-circle-markup (number->string mark))))

(define-public (format-mark-box-barnumbers mark context)
  (make-bold-markup (make-box-markup
    (number->string (ly:context-property context 'currentBarNumber)))))

(define-public (format-mark-circle-barnumbers mark context)
  (make-bold-markup (make-circle-markup
    (number->string (ly:context-property context 'currentBarNumber)))))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Bass figures.
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(define-public (format-bass-figure figure event context)
  (let* ((fig (ly:event-property event 'figure))
	 (fig-markup (if (number? figure)

			 ;; this is not very elegant, but center-aligning all digits
			 ;; is problematic with other markups, and shows problems
			 ;; in the (lack of) overshoot of feta alphabet glyphs.
			 
			 ((if (<= 10 figure)
			      (lambda (y) (make-translate-scaled-markup (cons -0.7 0) y))
			      identity)

			  (cond
				((eq? #t (ly:event-property event 'diminished))
				         (markup #:slashed-digit figure))
				((eq? #t (ly:event-property event 'augmented-slash))
				         (markup #:backslashed-digit figure))
				(else (markup #:number (number->string figure 10)))))
			 #f
			 ))
	 (alt (ly:event-property event 'alteration))
	 (alt-markup
	  (if (number? alt)
	      (markup
	       #:general-align Y DOWN #:fontsize
	       (if (not (= alt DOUBLE-SHARP))
		   -2 2)
	       (alteration->text-accidental-markup alt))
	      
	      #f))
	 (plus-markup (if (eq? #t (ly:event-property event 'augmented))
			  (markup #:number "+")
			  #f))

	 (alt-dir (ly:context-property context 'figuredBassAlterationDirection))
	 (plus-dir (ly:context-property context 'figuredBassPlusDirection))
	 )

    (if (and (not fig-markup) alt-markup)
	(begin
	  (set! fig-markup (markup #:left-align #:pad-around 0.3 alt-markup))
	  (set! alt-markup #f)))


    ;; hmm, how to get figures centered between note, and
    ;; lone accidentals too?
    
    ;;    (if (markup? fig-markup)
    ;;	(set!
    ;;	 fig-markup (markup #:translate (cons 1.0 0)
    ;;			    #:center-align fig-markup)))

    (if alt-markup
	(set! fig-markup
	      (markup #:put-adjacent
		      X (if (number? alt-dir)
			    alt-dir
			    LEFT)
		      fig-markup
		      #:pad-x 0.2 alt-markup
		      )))

    
    (if plus-markup
	(set! fig-markup
	      (if fig-markup
		  (markup #:put-adjacent
			  X (if (number? plus-dir)
				plus-dir
				LEFT)
			  fig-markup
			  #:pad-x 0.2 plus-markup)
		  plus-markup)))
    
    (if (markup? fig-markup)
	(markup #:fontsize -2 fig-markup)
	empty-markup)

    ))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; fret diagrams

(define-public (determine-frets context grob notes string-numbers)
  
  (define (ensure-number a b)
    (if (number? a)
	a
	b))

  (define (string-frets->dot-placement string-frets string-count)
    (let*
      ((desc (list->vector
              (map (lambda (x) (list 'mute  (1+ x)))
                   (iota string-count)))))

       (for-each (lambda (sf)
                   (let*
                       ((string (car sf))
                        (fret (cadr sf))
                        (finger (caddr sf)))

                       (vector-set! 
                         desc (1- string)
                         (if (= 0 fret)
                             (list 'open string)
                             (if finger
                                 (list 'place-fret string fret finger)
                                 (list 'place-fret string fret))
                                      ))
                     ))
                 string-frets)
       (vector->list desc)))

;; body.
  (let*
      ((tunings (ly:context-property context 'stringTunings))
       (my-string-count (length tunings))
       (details (ly:grob-property grob 'fret-diagram-details))
       (predefined-frets
         (ly:context-property context 'predefinedDiagramTable)) 
       (minimum-fret (ensure-number
		      (ly:context-property context 'minimumFret) 0))
       (max-stretch (ensure-number
		      (ly:context-property context 'maximumFretStretch) 4))
       (string-frets (determine-frets-mf notes string-numbers
					 minimum-fret max-stretch
					 tunings))
       (pitches (map (lambda (x) (ly:event-property x 'pitch)) notes)))

    (set! (ly:grob-property grob 'fret-diagram-details)

          (if (null? details)
              (acons 'string-count (length tunings) '())
              (acons 'string-count (length tunings) details)))
    (set! (ly:grob-property grob 'dot-placement-list)
        (if predefined-frets
            (let ((hash-handle 
                    (hash-get-handle
                      predefined-frets
                      (cons tunings pitches))))
              (if hash-handle 
                  (cdr hash-handle)  ;found default diagram
                  (string-frets->dot-placement 
                        string-frets my-string-count)))
            (string-frets->dot-placement string-frets my-string-count)))))

(define-public (determine-frets-mf notes string-numbers
				   minimum-fret max-stretch
				   tunings)

  (define (calc-fret pitch string tuning)
    (- (ly:pitch-semitones pitch) (list-ref tuning (1- string))))

  (define (note-pitch a)
    (ly:event-property a 'pitch))

  (define (note-pitch>? a b)
    (ly:pitch<? (note-pitch b)
		(note-pitch a)))

  (define (note-finger ev)
    (let* ((articulations (ly:event-property ev 'articulations))
	   (finger-found #f))

      (map (lambda (art)
	     (let*
		 ((num (ly:event-property art 'digit)))

	       (if (and (eq? 'fingering-event (ly:event-property art 'class))
			(number? num))
		   (set! finger-found num))))
	   articulations)

      finger-found))
  
  (define (note-string ev)
    (let* ((articulations (ly:event-property ev 'articulations))
	   (string-found #f))

      (map (lambda (art)
	     (let*
		 ((num (ly:event-property art 'string-number)))

	       (if (number? num)
		   (set! string-found num))))
	   articulations)

      string-found))

  (define (del-string string)
		      (if (number? string)
			  (set! free-strings
				(delete string free-strings))))
  (define specified-frets '())
  (define free-strings '())
  
  (define (close-enough fret)
		       (reduce
			(lambda (x y)
			  (and x y))
			#t
			(map (lambda (specced-fret)
			       (> max-stretch (abs (- fret specced-fret))))
			     specified-frets)
			))
  
  (define (string-qualifies string pitch)
    (let*
	((fret (calc-fret pitch string tunings)))
	 
	 (and (>= fret minimum-fret)
	      (close-enough fret))
	 
	 ))
			   
  (define string-fret-fingering-tuples '())
  (define (set-fret note string)
		    (set! string-fret-fingering-tuples
			  (cons (list string
				      (calc-fret (ly:event-property note 'pitch)
						 string tunings)
				      (note-finger note))
				string-fret-fingering-tuples))
		    (del-string string))
       

  ;;; body.
  (set! specified-frets
	(filter identity (map
		      (lambda (note)
			(if (note-string note)
			    (calc-fret (note-pitch note)
				       (note-string note) tunings)
			    #f))
		      notes)))


  (set! free-strings (map 1+ (iota (length tunings))))
    
  (for-each (lambda (note)
	      (del-string (note-string note)))
	    notes)
  
  
  (for-each
   (lambda (note)
     (if (note-string note)
	 (set-fret note (note-string note))
	 (let*
	     ((fit-string (find (lambda (string) 
                               (string-qualifies string (note-pitch note)))
			    free-strings)))
	   (if fit-string
	       (set-fret note fit-string)
	       (ly:warning "No string for pitch ~a (given frets ~a)" 
                           (note-pitch note)
			   specified-frets))
			   
	       )))
   (sort notes note-pitch>?))

  string-fret-fingering-tuples)
