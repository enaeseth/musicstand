;;;;
;;;; lily-library.scm -- utilities
;;;;
;;;;  source file of the GNU LilyPond music typesetter
;;;; 
;;;; (c) 1998--2009 Jan Nieuwenhuizen <janneke@gnu.org>
;;;; Han-Wen Nienhuys <hanwen@xs4all.nl>

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; constants.

(define-public X 0)
(define-public Y 1)
(define-safe-public START -1)
(define-safe-public STOP 1)
(define-public LEFT -1)
(define-public RIGHT 1)
(define-public UP 1)
(define-public DOWN -1)
(define-public CENTER 0)

(define-safe-public DOUBLE-FLAT-QTS -4)
(define-safe-public THREE-Q-FLAT-QTS -3)
(define-safe-public FLAT-QTS -2)
(define-safe-public SEMI-FLAT-QTS -1)
(define-safe-public NATURAL-QTS 0)
(define-safe-public SEMI-SHARP-QTS 1)
(define-safe-public SHARP-QTS 2)
(define-safe-public THREE-Q-SHARP-QTS 3)
(define-safe-public DOUBLE-SHARP-QTS 4)
(define-safe-public SEMI-TONE-QTS 2)

(define-safe-public DOUBLE-FLAT  -1)
(define-safe-public THREE-Q-FLAT -3/4)
(define-safe-public FLAT -1/2)
(define-safe-public SEMI-FLAT -1/4)
(define-safe-public NATURAL 0)
(define-safe-public SEMI-SHARP 1/4)
(define-safe-public SHARP 1/2)
(define-safe-public THREE-Q-SHARP 3/4)
(define-safe-public DOUBLE-SHARP 1)
(define-safe-public SEMI-TONE 1/2)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; moments

(define-public ZERO-MOMENT (ly:make-moment 0 1)) 

(define-public (moment-min a b)
  (if (ly:moment<? a b) a b))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; arithmetic
(define-public (average x . lst)
  (/ (+ x (apply + lst)) (1+ (length lst))))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; parser <-> output hooks.
		
(define-public (collect-bookpart-for-book parser book-part)
  "Toplevel book-part handler"
  (define (add-bookpart book-part)
    (ly:parser-define!
       parser 'toplevel-bookparts
       (cons book-part (ly:parser-lookup parser 'toplevel-bookparts))))
  ;; If toplevel scores have been found before this \bookpart,
  ;; add them first to a dedicated bookpart
  (if (pair? (ly:parser-lookup parser 'toplevel-scores))
      (begin
	(add-bookpart (ly:make-book-part
		       (ly:parser-lookup parser 'toplevel-scores)))
	(ly:parser-define! parser 'toplevel-scores (list))))
  (add-bookpart book-part))

(define-public (collect-scores-for-book parser score)
  (ly:parser-define!
   parser 'toplevel-scores
   (cons score (ly:parser-lookup parser 'toplevel-scores))))

(define-public (collect-music-aux score-handler parser music)
  (define (music-property symbol)
    (let ((value (ly:music-property music symbol)))
      (if (not (null? value))
	  value
	  #f)))
  (cond ((music-property 'page-marker)
	 ;; a page marker: set page break/turn permissions or label
	 (begin
	   (let ((label (music-property 'page-label)))
	     (if (symbol? label)
		 (score-handler (ly:make-page-label-marker label))))
	   (for-each (lambda (symbol)
		       (let ((permission (music-property symbol)))
			 (if (symbol? permission)
			     (score-handler
			      (ly:make-page-permission-marker symbol
							      (if (eqv? 'forbid permission)
								  '()
								  permission))))))
		     (list 'line-break-permission 'page-break-permission
			   'page-turn-permission))))
	((not (music-property 'void))
	 ;; a regular music expression: make a score with this music
	 ;; void music is discarded
	 (score-handler (scorify-music music parser)))))

(define-public (collect-music-for-book parser music)
  "Top-level music handler"
  (collect-music-aux (lambda (score)
		       (collect-scores-for-book parser score))
                     parser
		     music))

(define-public (collect-book-music-for-book parser book music)
  "Book music handler"
  (collect-music-aux (lambda (score)
		       (ly:book-add-score! book score))
                     parser
		     music))

(define-public (scorify-music music parser)
  "Preprocess MUSIC."
  
  (for-each (lambda (func)
	      (set! music (func music parser)))
	    toplevel-music-functions)

  (ly:make-score music))

(define (print-book-with parser book process-procedure)
  (let*
      ((paper (ly:parser-lookup parser '$defaultpaper))
       (layout (ly:parser-lookup parser '$defaultlayout))
       (count (ly:parser-lookup parser 'output-count))
       (base (ly:parser-output-name parser))
       (output-suffix (ly:parser-lookup parser 'output-suffix)) )

    (if (string? output-suffix)
	(set! base (format "~a-~a" base (string-regexp-substitute
					   "[^a-zA-Z0-9-]" "_" output-suffix))))

    ;; must be careful: output-count is under user control.
    (if (not (integer? count))
	(set! count 0))

    (if (> count 0)
	(set! base (format #f "~a-~a" base count)))
    (ly:parser-define! parser 'output-count (1+ count))
    (process-procedure book paper layout base)
    ))

(define-public (print-book-with-defaults parser book)
  (print-book-with parser book ly:book-process))

(define-public (print-book-with-defaults-as-systems parser book)
  (print-book-with parser book ly:book-process-to-systems))

;;;;;;;;;;;;;;;;
;; alist

(define-public assoc-get ly:assoc-get)

(define-public (uniqued-alist alist acc)
  (if (null? alist) acc
      (if (assoc (caar alist) acc)
	  (uniqued-alist (cdr alist) acc)
	  (uniqued-alist (cdr alist) (cons (car alist) acc)))))

(define-public (alist<? x y)
  (string<? (symbol->string (car x))
	    (symbol->string (car y))))

(define-public (chain-assoc-get x alist-list . default)
  "Return ALIST entry for X. Return DEFAULT (optional, else #f) if not
found."

  (define (helper x alist-list default)
    (if (null? alist-list)
	default
	(let* ((handle (assoc x (car alist-list))))
	  (if (pair? handle)
	      (cdr handle)
	      (helper x (cdr alist-list) default)))))

  (helper x alist-list
	  (if (pair? default) (car default) #f)))

(define (map-alist-vals func list)
  "map FUNC over the vals of  LIST, leaving the keys."
  (if (null?  list)
      '()
      (cons (cons  (caar list) (func (cdar list)))
	    (map-alist-vals func (cdr list)))))

(define (map-alist-keys func list)
  "map FUNC over the keys of an alist LIST, leaving the vals. "
  (if (null?  list)
      '()
      (cons (cons (func (caar list)) (cdar list))
	    (map-alist-keys func (cdr list)))))

(define-public (first-member members lst)
  "Return first successful MEMBER of member from MEMBERS in LST."
  (if (null? members)
      #f
      (let ((m (member (car members) lst)))
	(if m m (first-member (cdr members) lst)))))

(define-public (first-assoc keys lst)
  "Return first successful ASSOC of key from KEYS in LST."
  (if (null? keys)
      #f
      (let ((k (assoc (car keys) lst)))
	(if k k (first-assoc (cdr keys) lst)))))

(define-public (flatten-alist alist)
  (if (null? alist)
      '()
      (cons (caar alist)
	    (cons (cdar alist)
		  (flatten-alist (cdr alist))))))

;;;;;;;;;;;;;;;;
;; vector

(define-public (vector-for-each proc vec)
  (do
      ((i 0 (1+ i)))
      ((>= i (vector-length vec)) vec)
    (vector-set! vec i (proc (vector-ref vec i)))))

;;;;;;;;;;;;;;;;
;; hash

(define-public (hash-table->alist t)
  (hash-fold (lambda (k v acc) (acons  k v  acc))
	     '() t))

;; todo: code dup with C++. 
(define-safe-public (alist->hash-table lst)
  "Convert alist to table"
  (let ((m (make-hash-table (length lst))))
    (map (lambda (k-v) (hashq-set! m (car k-v) (cdr k-v))) lst)
    m))

;;;;;;;;;;;;;;;;
;; list

(define (functional-or . rest)
  (if (pair? rest)
      (or (car rest)
	   (apply functional-and (cdr rest)))
      #f))

(define (functional-and . rest)
  (if (pair? rest)
      (and (car rest)
	   (apply functional-and (cdr rest)))
      #t))

(define (split-list lst n)
  "Split LST in N equal sized parts"
  
  (define (helper todo acc-vector k)
    (if (null? todo)
	acc-vector
	(begin
	  (if (< k 0)
	      (set! k (+ n k)))
	    
	  (vector-set! acc-vector k (cons (car todo) (vector-ref acc-vector k)))
	  (helper (cdr todo) acc-vector (1- k)))))

  (helper lst (make-vector n '()) (1- n)))

(define (list-element-index lst x)
  (define (helper todo k)
    (cond
     ((null? todo) #f)
     ((equal? (car todo) x) k)
     (else
      (helper (cdr todo) (1+ k)))))

  (helper lst 0))

(define-public (count-list lst)
  "Given lst (E1 E2 .. ) return ((E1 . 1) (E2 . 2) ... )  "

  (define (helper l acc count)
    (if (pair? l)
	(helper (cdr l) (cons (cons (car l) count) acc) (1+ count))
	acc))


  (reverse (helper lst '() 1)))
  
(define-public (list-join lst intermediate)
  "put INTERMEDIATE  between all elts of LST."

  (fold-right
   (lambda (elem prev)
	    (if (pair? prev)
		(cons  elem (cons intermediate prev))
		(list elem)))
	  '() lst))

(define-public (filtered-map proc lst)
  (filter
   (lambda (x) x)
   (map proc lst)))


(define (flatten-list lst)
  "Unnest LST" 
  (if (null? lst)
      '()
      (if (pair? (car lst))
	  (append (flatten-list (car lst)) (flatten-list  (cdr lst)))
	  (cons (car lst) (flatten-list (cdr lst))))))

(define (list-minus a b)
  "Return list of elements in A that are not in B."
  (lset-difference eq? a b))

(define-public (uniq-list lst)
  "Uniq LST, assuming that it is sorted. Uses equal? for comparisons."

  (reverse! 
   (fold (lambda (x acc)
	   (if (null? acc)
	       (list x)
	       (if (equal? x (car acc))
		   acc
		   (cons x acc))))
	 '() lst) '()))

(define (split-at-predicate predicate lst)
 "Split LST = (a_1 a_2 ... a_k b_1 ... b_k)
  into L1 = (a_1 ... a_k ) and L2 =(b_1 .. b_k) 
  Such that (PREDICATE a_i a_{i+1}) and not (PREDICATE a_k b_1).
  L1 is copied, L2 not.

  (split-at-predicate (lambda (x y) (= (- y x) 2)) '(1 3 5 9 11) (cons '() '()))"
 
 ;; " Emacs is broken

 (define (inner-split predicate lst acc)
   (cond
    ((null? lst) acc)
    ((null? (cdr lst))
     (set-car! acc (cons (car lst) (car acc)))
     acc)
    ((predicate (car lst) (cadr lst))
     (set-car! acc (cons (car lst) (car acc)))
     (inner-split predicate (cdr lst) acc))
    (else
     (set-car! acc (cons (car lst) (car acc)))
     (set-cdr! acc (cdr lst))
     acc)))
 
 (let* ((c (cons '() '())))
   (inner-split predicate lst  c)
   (set-car! c (reverse! (car c)))
   c))

(define-public (split-list-by-separator lst sep?)
   "(display (split-list-by-separator '(a b c / d e f / g) (lambda (x) (equal? x '/))))
   =>
   ((a b c) (d e f) (g))
  "
   ;; " Emacs is broken
   (define (split-one sep?  lst acc)
     "Split off the first parts before separator and return both parts."
     (if (null? lst)
	 (cons acc '())
	 (if (sep? (car lst))
	     (cons acc (cdr lst))
	     (split-one sep? (cdr lst) (cons (car lst) acc)))))
   
   (if (null? lst)
       '()
       (let* ((c (split-one sep? lst '())))
	 (cons (reverse! (car c) '()) (split-list-by-separator (cdr c) sep?)))))

(define-public (offset-add a b)
  (cons (+ (car a) (car b))
	(+ (cdr a) (cdr b)))) 

(define-public (offset-flip-y o)
  (cons (car o) (- (cdr o))))

(define-public (offset-scale o scale)
  (cons (* (car o) scale)
	(* (cdr o) scale)))

(define-public (ly:list->offsets accum coords)
  (if (null? coords)
      accum
      (cons (cons (car coords) (cadr coords))
	    (ly:list->offsets accum (cddr coords)))))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; numbers

(if (not (defined? 'nan?)) ;; guile 1.6 compat
    (define-public (nan? x) (not (or (< 0.0 x)
				     (> 0.0 x)
				     (= 0.0 x)))))

(if (not (defined? 'inf?))
    (define-public (inf? x) (= (/ 1.0 x) 0.0)))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; intervals

(define-public (interval-length x)
  "Length of the number-pair X, when an interval"
  (max 0 (- (cdr x) (car x))))

(define-public interval-start car)
(define-public (ordered-cons a b)
  (cons (min a b)
	(max a b)))

(define-public interval-end cdr)

(define-public (interval-bound interval dir)
  ((if (= dir RIGHT) cdr car) interval))

(define-public (interval-index interval dir)
  "Interpolate INTERVAL between between left (DIR=-1) and right (DIR=+1)"
  
  (* (+  (interval-start interval) (interval-end interval)
	 (* dir (- (interval-end interval) (interval-start interval))))
     0.5))

(define-public (interval-center x)
  "Center the number-pair X, when an interval"
  (if (interval-empty? x)
      0.0
      (/ (+ (car x) (cdr x)) 2)))

(define-public interval-start car)
(define-public interval-end cdr)
(define-public (interval-translate iv amount)
  (cons (+ amount (car iv))
	(+ amount (cdr iv))))

(define (other-axis a)
  (remainder (+ a 1) 2))

(define-public (interval-widen iv amount)
   (cons (- (car iv) amount)
         (+ (cdr iv) amount)))


(define-public (interval-empty? iv)
   (> (car iv) (cdr iv)))

(define-public (interval-union i1 i2)
   (cons (min (car i1) (car i2))
	 (max (cdr i1) (cdr i2))))

(define-public (interval-sane? i)
  (not (or  (nan? (car i))
	    (inf? (car i))
	    (nan? (cdr i))
	    (inf? (cdr i))
	    (> (car i) (cdr i)))))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; string

(define-public (string-endswith s suffix)
  (equal? suffix (substring s
			    (max 0 (- (string-length s) (string-length suffix)))
			    (string-length s))))
	     
(define-public (string-startswith s prefix)
  (equal? prefix (substring s 0 (min (string-length s) (string-length prefix)))))
	     
(define-public (string-encode-integer i)
  (cond
   ((= i  0) "o")
   ((< i 0)   (string-append "n" (string-encode-integer (- i))))
   (else (string-append
	  (make-string 1 (integer->char (+ 65 (modulo i 26))))
	  (string-encode-integer (quotient i 26))))))

(define (number->octal-string x)
  (let* ((n (inexact->exact x))
         (n64 (quotient n 64))
         (n8 (quotient (- n (* n64 64)) 8)))
    (string-append
     (number->string n64)
     (number->string n8)
     (number->string (remainder (- n (+ (* n64 64) (* n8 8))) 8)))))

(define-public (ly:inexact->string x radix)
  (let ((n (inexact->exact x)))
    (number->string n radix)))

(define-public (ly:number-pair->string c)
  (string-append (ly:number->string (car c)) " "
		 (ly:number->string (cdr c))))

(define-public (dir-basename file . rest)
  "Strip suffixes in REST, but leave directory component for FILE."
  (define (inverse-basename x y) (basename y x))
  (simple-format #f "~a/~a" (dirname file)
		 (fold inverse-basename file rest)))

(define-public (write-me message x)
  "Return X.  Display MESSAGE and write X.  Handy for debugging,
possibly turned off."
  (display message) (write x) (newline) x)
;;  x)

(define-public (stderr string . rest)
  (apply format (cons (current-error-port) (cons string rest)))
  (force-output (current-error-port)))

(define-public (debugf string . rest)
  (if #f
      (apply stderr (cons string rest))))

(define (index-cell cell dir)
  (if (equal? dir 1)
      (cdr cell)
      (car cell)))

(define (cons-map f x)
  "map F to contents of X"
  (cons (f (car x)) (f (cdr x))))

(define-public (list-insert-separator lst between)
  "Create new list, inserting BETWEEN between elements of LIST"
  (define (conc x y )
    (if (eq? y #f)
	(list x)
	(cons x  (cons between y))))
  (fold-right conc #f lst))

(define-public (string-regexp-substitute a b str)
  (regexp-substitute/global #f a str 'pre b 'post)) 

(define (regexp-split str regex)
  (define matches '())
  (define end-of-prev-match 0)
  (define (notice match)

    (set! matches (cons (substring (match:string match)
				   end-of-prev-match
				   (match:start match))
			matches))
    (set! end-of-prev-match (match:end match)))

  (regexp-substitute/global #f regex str notice 'post)

  (if (< end-of-prev-match (string-length str))
      (set!
       matches
       (cons (substring str end-of-prev-match (string-length str)) matches)))

   (reverse matches))

;;;;;;;;;;;;;;;;
; other
(define (sign x)
  (if (= x 0)
      0
      (if (< x 0) -1 1)))


(define-public (car< a b)
  (< (car a) (car b)))

(define-public (symbol<? lst r)
  (string<? (symbol->string lst) (symbol->string r)))

(define-public (symbol-key<? lst r)
  (string<? (symbol->string (car lst)) (symbol->string (car r))))

;;
;; don't confuse users with #<procedure .. > syntax. 
;; 
(define-public (scm->string val)
  (if (and (procedure? val)
	   (symbol? (procedure-name val)))
      (symbol->string (procedure-name val))
      (string-append
       (if (self-evaluating? val)
	   (if (string? val)
	       "\""
	       "")
	   "'")
       (call-with-output-string (lambda (port) (display val port)))
       (if (string? val)
	   "\""
	   ""))))

(define-public (!= lst r)
  (not (= lst r)))

(define-public lily-unit->bigpoint-factor
  (cond
   ((equal? (ly:unit) "mm") (/ 72.0 25.4))
   ((equal? (ly:unit) "pt") (/ 72.0 72.27))
   (else (ly:error (_ "unknown unit: ~S") (ly:unit)))))

(define-public lily-unit->mm-factor
  (* 25.4 (/ lily-unit->bigpoint-factor 72)))

;;; FONT may be font smob, or pango font string...
(define-public (font-name-style font)
      ;; FIXME: ughr, (ly:font-name) sometimes also has Style appended.
      (let* ((font-name (ly:font-name font))
	     (full-name (if font-name font-name (ly:font-file-name font)))
	     (name-style (string-split full-name #\-)))
	;; FIXME: ughr, barf: feta-alphabet is actually emmentaler
	(if (string-prefix? "feta-alphabet" full-name)
	    (list "emmentaler"
		  (substring  full-name (string-length "feta-alphabet")))
	    (if (not (null? (cdr name-style)))
	    name-style
	    (append name-style '("Regular"))))))

(define-public (modified-font-metric-font-scaling font)
  (let* ((designsize (ly:font-design-size font))
	 (magnification (* (ly:font-magnification font)))
	 (scaling (* magnification designsize)))
    (debugf "scaling:~S\n" scaling)
    (debugf "magnification:~S\n" magnification)
    (debugf "design:~S\n" designsize)
    scaling))

(define-public (version-not-seen-message input-file-name)
  (ly:message
   "~a:0: ~a: ~a" 
    input-file-name
    (_ "warning: ")
    (format #f
	    (_ "no \\version statement found, please add~afor future compatibility")
	    (format #f "\n\n\\version ~s\n\n" (lilypond-version)))))

(define-public (old-relative-not-used-message input-file-name)
  (ly:message
   "~a:0: ~a: ~a" 
    input-file-name
    (_ "warning: ")
    (_ "old relative compatibility not used")))
