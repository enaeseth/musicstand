;;
;; clip-region.scm -- implement  rhythmic-location and EPS musical clipping 
;; 
;; source file of the GNU LilyPond music typesetter
;; 
;; (c) 2006 Han-Wen Nienhuys <hanwen@lilypond.org>
;; 

(define-module (scm clip-region))

(use-modules (lily))


(define-public (make-rhythmic-location bar-num num den)
  (cons
   bar-num (ly:make-moment num den)))

(define-public (rhythmic-location? a)
  (and (pair? a)
       (integer? (car a))
       (ly:moment? (cdr a))))

(define-public (make-graceless-rhythmic-location loc)
  (make-rhythmic-location
   (car loc)
   (ly:moment-main-numerator (rhythmic-location-measure-position loc))
   (ly:moment-main-denominator (rhythmic-location-measure-position loc))))
		   
					     
(define-public rhythmic-location-measure-position cdr)
(define-public rhythmic-location-bar-number car)

(define-public (rhythmic-location<? a b)
  (cond
   ((< (car a) (car b)) #t)
   ((> (car a) (car b)) #f)
   (else
    (ly:moment<? (cdr a) (cdr b)))))

(define-public (rhythmic-location<=? a b)
  (not (rhythmic-location<? b a)))
(define-public (rhythmic-location>=? a b)
  (rhythmic-location<? a b))
(define-public (rhythmic-location>? a b)
  (rhythmic-location<? b a))

(define-public (rhythmic-location=? a b)
  (and (rhythmic-location<=? a b)
       (rhythmic-location<=? b a)))


(define-public (rhythmic-location->file-string a)
  (ly:format "~a.~a.~a"
	  (car a)
	  (ly:moment-main-numerator (cdr a))
	  (ly:moment-main-denominator (cdr a))))

(define-public (rhythmic-location->string a)
  (ly:format "bar ~a ~a"
	  (car a)
	  (ly:moment->string  (cdr a))))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;  Actual clipping logic.

;;
;; the total of this will be
;; O(#systems * #regions)
;; 
;; we can actually do better by sorting the regions as well,
;; but let's leave that for future extensions.
;;
(define-public (system-clipped-x-extent system-grob clip-region)
  "Return the X-extent of the SYSTEM-GROB when clipped with
CLIP-REGION. Return #f if not appropriate."
  
  (let*
      ((region-start (car clip-region))
       (columns (ly:grob-object system-grob 'columns))
       (region-end (cdr clip-region))
       (found-grace-end  #f)
       (candidate-columns 
	(filter
	 (lambda (j)
	   (let*
	       ((column (ly:grob-array-ref columns j))
		(loc (ly:grob-property column 'rhythmic-location))
		(grace-less (make-graceless-rhythmic-location loc))
		)
		
	     (and (rhythmic-location? loc)
		  (rhythmic-location<=? region-start loc)
		  (or (rhythmic-location<? grace-less region-end)
		      (and (rhythmic-location=? grace-less region-end)
			   (eq? #t (ly:grob-property column 'non-musical))

			   )))

	     ))
	 
	 (iota (ly:grob-array-length columns))))
       
       (column-range
	(if (>= 1 (length candidate-columns))
	    #f
	    (cons (car candidate-columns)
		  (car (last-pair candidate-columns)))))

       (clipped-x-interval
	(if column-range
	    (cons

	     (interval-start
	      (ly:grob-robust-relative-extent
	       (if (= 0 (car column-range))
		   system-grob
		   (ly:grob-array-ref columns (car column-range)))
	       system-grob X))
	     
	     (interval-end
	      (ly:grob-robust-relative-extent
	      (if (= (1- (ly:grob-array-length columns)) (cdr column-range))
		  system-grob
		  (ly:grob-array-ref columns (cdr column-range)))
	      system-grob X)))
	    
	    
	    #f
	    )))
    
    clipped-x-interval))
