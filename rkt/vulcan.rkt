#lang racket/base

(require racket/match)

(struct Datum (value) #:transparent)
(struct Ref (i) #:transparent)
(struct Prim (name rands) #:transparent)
(struct Clos (arity fvi* ntmps body) #:transparent)
(struct App (rator rands) #:transparent)
(struct If (tst conseq alt) #:transparent)
(struct Let (i* rhs* body) #:transparent)
(struct Fix (i* rhs* body) #:transparent)
(struct Seq (e*) #:transparent)

(struct KLet (e i rhs* body) #:transparent)
(struct KSeq (e rest) #:transparent)

(struct closure (arity fvv* ntmps body) #:transparent)

(define (make-closure e arity fvi* ntmps body)
  (define fvv^ (for/vector ([i (in-list fvi*)]) (vector-ref e i)))
  (closure arity fvv^ ntmps body))

(define (value? v)
  (or (closure? v) (number? v) (boolean? v)))

(define (make-environment arity rands fv* ntmps)
  (unless (= arity (length rands))
    (error 'apply-closure "arity" arity (length rands)))
  (define e (make-vector (+ arity (vector-length fv*) ntmps)))
  (for ([(r i) (in-indexed (in-list rands))])
    (vector-set! e i r))
  (for ([(v i) (in-indexed fv*)])
    (vector-set! e (+ i arity) (vector-ref fv* i)))
  e)

(define (apply-prim name e k rands*)
  (match* (name rands*)
    [('+     (list a b)) (values (+ a b) e k)]
    [('=     (list a b)) (values (= a b) e k)]
    [('sub1  (list a))   (values (sub1 a) e k)]
    [('zero? (list a))   (values (zero? a) e k)]
    ))

(define (evatom e c)
  (match c
    [(Datum v) v]
    [(Ref i) (vector-ref e i)]
    [(Clos arity fv* ntmps body) (make-closure e arity fv* ntmps body)]
    [_ (error 'evatom "not an atomic expression: ~v" c)]))

(define (evatom* e c*)
  (for/list ([c (in-list c*)]) (evatom e c)))

(define (step c e k)
  (define (apply-closure cl rands)
    (match-define (closure arity fv* ntmps body) cl)

    (define e (make-environment arity rands fv* ntmps))
    (values (closure-body cl) e k))

  (match c
    [(or (? Datum?) (? Ref?) (? Clos?)) (values (evatom e c) e k)]
    [(Prim name rands)
     (apply-prim name e k (evatom* e rands))]
    [(App rator rands)
     (apply-closure (evatom e rator) (evatom* e rands))]
    [(If test conseq alt)
     (values (if (evatom e test) conseq alt) e k)]
    [(Let i* rhs* body)
     (values (car rhs*) e (cons (KLet e i* (cdr rhs*) body) k))]
    [(Seq (cons c c*))
     (values c e (cons (KSeq e c*) k))]
    [(Fix i* rhs* body)
     ;; assign closures to env slots
     (for ([i (in-list i*)]
           [p (in-list rhs*)])
       (match-define (Clos arity fv* ntmps body) p)
       (vector-set! e i (make-closure e arity fv* ntmps body)))
     ;; patch closure environments to use new values
     (for ([i (in-list i*)]
           [p (in-list rhs*)]
           #:do [(define f (vector-ref e i))
                 (define fe (closure-fvv* f))]
           #:when #t
           [k (in-naturals)]
           [fvi (in-list (Clos-fvi* p))]
           #:when (member fvi i*))
       (vector-set! fe k (vector-ref e fvi)))
     ;; continue to body
     (values body e k)]))


(define (ev c ntmps)
  (define (step* c e k)
    (cond
      [(value? c) (cont k c)]
      [else
       (call-with-values
        (λ () (step c e k))
        step*)]))
  (define (cont k v)
    (match k
      [(list) v]
      [(cons (KLet e (list i) (list) body) k)
       (vector-set! e i v)
       (step* body e k)]
      [(cons (KLet e (cons i i*) (cons rhs rhs*) body) k)
       (vector-set! e i v)
       (step* rhs e (cons (KLet e i* rhs* body) k))]
      [(cons (KSeq e (list c)) k)
       (step* c e k)]
      [(cons (KSeq e (cons c c*)) k)
       (step* c e (cons (KSeq e c*) k))]))
  (step* c (make-vector ntmps) null))


#;
(ev (Let 0 (list (Clos 0 null 0 (Prim '+ (list (Datum 3) (Datum 4)))))
         (App (Ref 0) null))
    1)
#;
(ev (Let 0 (list (Datum 3) (Datum 10)) (Prim '+ (list (Ref 0) (Ref 1))))
    2)

(ev (Fix '(0 1)
         (list (Clos 1 '(1) 2 ;; #(x even? t s)
                     (Let '(2)
                          (list (Prim '= (list (Ref 0) (Datum 1))))
                          (If (Ref 2)
                              (Ref 2)
                              (Let '(3)
                                   (list (Prim 'sub1 (list (Ref 0))))
                                   (App (Ref 1) (list (Ref 3)))))))

               (Clos 1 '(0) 2 ;; #(x odd? t s)
                     (Let '(2)
                          (list (Prim 'zero? (list (Ref 0))))
                          (If (Ref 2)
                              (Ref 2)
                              (Let '(3)
                                   (list (Prim 'sub1 (list (Ref 0))))
                                   (App (Ref 1) (list (Ref 3))))))))
         (App (Ref 0) (list (Datum 21))))
    2)
