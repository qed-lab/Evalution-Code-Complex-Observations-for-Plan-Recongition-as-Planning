
(define (problem blocks_words)
	(:domain blocks)
(:objects 

d r a w o e p c - block
)
(:init
(handempty)
(clear o)
(ontable o)
(clear r)
(on r p)
(ontable p)
(clear e)
(ontable e)
(clear d)
(on d a)
(on a c)
(ontable c)
(clear w)
(ontable w)
)
(:goal (and
(clear w)
(ontable e)
(on w a)
(on a d)
(on d e)
))
)
